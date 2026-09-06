"""The run ledger.

Every measurement PSA reports is computed from this file alone. The boundary
between execution and analysis is the whole point: a third party must be able
to recompute the numbers without re-running an agent.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    catalog_source: str
    catalog_commit: str
    stage: str                    # "pilot" | "screening" | "exact" | "validation"
    config_index: int
    skills_assigned: tuple[str, ...]
    skills_invoked: tuple[str, ...]   # the ITT / treated distinction lives here
    task_id: str
    seed: int
    model: str
    harness: str
    resolved: bool
    f2p_fraction: float
    turns: int
    tokens: int
    wall_seconds: float
    notes: dict = field(default_factory=dict)


def append(path: str | Path, record: RunRecord) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def load(path: str | Path) -> list[RunRecord]:
    records = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        raw["skills_assigned"] = tuple(raw["skills_assigned"])
        raw["skills_invoked"] = tuple(raw["skills_invoked"])
        records.append(RunRecord(**raw))
    return records


def value_table(
    records: Iterable[RunRecord],
    tasks: Sequence[str],
    outcome: str = "resolved",
    treated_only: bool = False,
) -> dict[frozenset, np.ndarray]:
    """Collapse a ledger into ``{coalition: per-task mean outcome}``.

    ``treated_only`` switches the analysis from intention-to-treat (the skill
    was assigned) to effect-among-invoked (the skill was actually used). Both
    are reported; the gap between them is control 7.2 of the design document.
    """
    index = {t: i for i, t in enumerate(tasks)}
    sums: dict[frozenset, np.ndarray] = {}
    counts: dict[frozenset, np.ndarray] = {}
    for r in records:
        key = frozenset(r.skills_invoked if treated_only else r.skills_assigned)
        if r.task_id not in index:
            continue
        if key not in sums:
            sums[key] = np.zeros(len(tasks))
            counts[key] = np.zeros(len(tasks))
        value = float(getattr(r, outcome))
        sums[key][index[r.task_id]] += value
        counts[key][index[r.task_id]] += 1
    table = {}
    for key, total in sums.items():
        n = counts[key]
        if (n == 0).any():
            missing = [tasks[i] for i in np.flatnonzero(n == 0)]
            raise ValueError(
                f"coalition {sorted(key) or '(empty)'} has no run for tasks {missing}; "
                "the paired design requires every coalition on every task"
            )
        table[key] = total / n
    return table
