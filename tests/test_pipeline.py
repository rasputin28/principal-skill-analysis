"""End-to-end wiring, exercised with the stub runner.

The point of this test is that on the night of a real run nothing structural
is discovered for the first time: catalog, design, compilation, ledger and
estimation are already known to fit together.
"""

import numpy as np
import pytest

from psa import catalog as catalog_mod
from psa import compile as compile_mod
from psa import design as design_mod
from psa import estimate as estimate_mod
from psa import ledger as ledger_mod
from psa import report as report_mod
from psa.runner import StubRunner


SKILLS = {
    "planner": "Plan before implementing.",
    "tester": "Write the failing test first.",
    "placebo": "This document describes the repository layout in general terms.",
}


@pytest.fixture
def fake_catalog(tmp_path):
    root = tmp_path / "catalog"
    for name, body in SKILLS.items():
        d = root / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {body}\n---\n\n{body * 20}\n"
        )
    return catalog_mod.discover(root)


def test_catalog_discovers_and_pins(fake_catalog):
    assert sorted(fake_catalog.ids) == ["placebo", "planner", "tester"]
    assert fake_catalog.commit == "unversioned"
    assert all(s.approx_tokens > 0 for s in fake_catalog.skills)
    assert catalog_mod.median_tokens(fake_catalog) > 0


def test_duplicate_skill_ids_are_rejected(tmp_path):
    for i in (1, 2):
        d = tmp_path / f"copy{i}" / "dup"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nname: dup\n---\nbody\n")
    with pytest.raises(ValueError, match="duplicate skill id"):
        catalog_mod.discover(tmp_path)


def test_compilation_is_hermetic(fake_catalog, tmp_path):
    ws = compile_mod.compile_workspace(fake_catalog, ["planner"], tmp_path / "ws")
    compile_mod.assert_hermetic(fake_catalog, ["planner"], ws)
    assert (ws / "planner" / "SKILL.md").exists()
    assert not (ws / "tester").exists()


def test_hermeticity_check_catches_a_leak(fake_catalog, tmp_path):
    ws = compile_mod.compile_workspace(fake_catalog, ["planner"], tmp_path / "ws")
    (ws / "tester").mkdir()
    with pytest.raises(AssertionError, match="leaked"):
        compile_mod.assert_hermetic(fake_catalog, ["planner"], ws)


def test_full_loop_with_the_stub(fake_catalog, tmp_path):
    ids = sorted(fake_catalog.ids)
    matrix = design_mod.full_factorial(len(ids))
    configs = design_mod.configurations(matrix, ids)
    runner = StubRunner()
    tasks = [f"task-{i}" for i in range(6)]
    path = tmp_path / "ledger.jsonl"

    for cfg in configs:
        ws = compile_mod.compile_workspace(fake_catalog, cfg.skills, tmp_path / f"ws{cfg.index}")
        compile_mod.assert_hermetic(fake_catalog, cfg.skills, ws)
        for task in tasks:
            outcome = runner.run(task, ws, cfg.skills, seed=0)
            ledger_mod.append(
                path,
                ledger_mod.RunRecord(
                    run_id=f"{cfg.index}-{task}",
                    catalog_source=fake_catalog.source,
                    catalog_commit=fake_catalog.commit,
                    stage="exact",
                    config_index=cfg.index,
                    skills_assigned=cfg.skills,
                    skills_invoked=outcome.skills_invoked,
                    task_id=task,
                    seed=0,
                    model=runner.model,
                    harness=runner.name,
                    resolved=outcome.resolved,
                    f2p_fraction=outcome.f2p_fraction,
                    turns=outcome.turns,
                    tokens=outcome.tokens,
                    wall_seconds=outcome.wall_seconds,
                ),
            )

    records = ledger_mod.load(path)
    assert len(records) == len(configs) * len(tasks)

    values = ledger_mod.value_table(records, tasks, outcome="f2p_fraction")
    assert len(values) == 2 ** len(ids)

    phi = estimate_mod.shapley_exact_by_task(values, ids)
    assert estimate_mod.efficiency_residual(phi, values, ids) < 1e-12

    intervals = estimate_mod.bootstrap_ci(phi, ids, n_boot=200, seed=1)
    assert set(intervals) == set(ids)

    # And the guard must refuse to let stub numbers become a result.
    with pytest.raises(report_mod.UnpublishableLedger):
        report_mod.guard([r.harness for r in records])


def test_value_table_requires_the_paired_design(fake_catalog, tmp_path):
    path = tmp_path / "partial.jsonl"
    ledger_mod.append(
        path,
        ledger_mod.RunRecord(
            run_id="x", catalog_source="s", catalog_commit="c", stage="exact",
            config_index=0, skills_assigned=("planner",), skills_invoked=("planner",),
            task_id="t1", seed=0, model="m", harness="h", resolved=True,
            f2p_fraction=1.0, turns=1, tokens=1, wall_seconds=1.0,
        ),
    )
    records = ledger_mod.load(path)
    with pytest.raises(ValueError, match="paired design"):
        ledger_mod.value_table(records, ["t1", "t2"])


def test_itt_and_treated_tables_differ_when_a_skill_is_never_invoked(tmp_path):
    path = tmp_path / "itt.jsonl"
    for task in ("t1", "t2"):
        for assigned, invoked in ((("a",), ()), ((), ())):
            ledger_mod.append(
                path,
                ledger_mod.RunRecord(
                    run_id=f"{task}-{assigned}", catalog_source="s", catalog_commit="c",
                    stage="exact", config_index=0, skills_assigned=assigned,
                    skills_invoked=invoked, task_id=task, seed=0, model="m", harness="h",
                    resolved=True, f2p_fraction=1.0, turns=1, tokens=1, wall_seconds=1.0,
                ),
            )
    records = ledger_mod.load(path)
    itt = ledger_mod.value_table(records, ["t1", "t2"])
    treated = ledger_mod.value_table(records, ["t1", "t2"], treated_only=True)
    assert frozenset({"a"}) in itt
    assert frozenset({"a"}) not in treated  # assigned but never invoked


def test_controls_verdict_fails_a_significant_placebo():
    ok, notes = report_mod.controls_verdict(
        placebo=estimate_mod.Interval(0.05, 0.01, 0.09), saboteur=None
    )
    assert not ok
    assert any("NEGATIVE CONTROL FAILED" in n for n in notes)


def test_controls_verdict_passes_a_null_placebo():
    ok, notes = report_mod.controls_verdict(
        placebo=estimate_mod.Interval(0.001, -0.02, 0.02),
        saboteur=estimate_mod.Interval(-0.08, -0.12, -0.04),
    )
    assert ok


def test_placebo_matches_the_catalog_median_length(fake_catalog, tmp_path):
    from psa import controls

    target = catalog_mod.median_tokens(fake_catalog)
    path = controls.make_placebo(target, tmp_path / "controls")
    written = catalog_mod.discover(tmp_path / "controls")
    placebo = next(s for s in written.skills if s.id == controls.PLACEBO_ID)
    assert placebo.approx_tokens >= target
    assert placebo.approx_tokens < target + len(controls._PLACEBO_FILLER) / 4 + 60


def test_saboteur_is_written_and_discoverable(tmp_path):
    from psa import controls

    controls.make_saboteur(tmp_path / "controls")
    cat = catalog_mod.discover(tmp_path / "controls")
    assert cat.ids == [controls.SABOTEUR_ID]


def test_report_card_names_redundancy_when_it_finds_it():
    import numpy as np

    from psa import estimate as est

    intervals = {
        "planner": est.Interval(0.08, 0.02, 0.14),
        "tester": est.Interval(0.01, -0.03, 0.05),
    }
    matrix = np.array([[0.0, -0.06], [-0.06, 0.0]])
    text = report_mod.report_card(
        "src", "abc123", intervals, residual=0.0,
        interactions=(["planner", "tester"], matrix),
        best=[(("planner",), 0.61), (("planner", "tester"), 0.60)],
        control_notes=["negative control passed"],
    )
    assert "redundancy" in text
    assert "1/1 pairs interact negatively" in text
    assert "Best measured combinations" in text
