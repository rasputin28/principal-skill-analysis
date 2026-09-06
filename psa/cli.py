"""Command line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from . import catalog as catalog_mod
from . import design as design_mod
from . import estimate as estimate_mod
from . import ledger as ledger_mod
from . import report as report_mod


def _cmd_catalog(args: argparse.Namespace) -> int:
    cat = catalog_mod.discover(args.path)
    out = Path(args.out)
    cat.to_json(out)
    print(f"{len(cat.skills)} skills at commit {cat.commit[:12]} -> {out}")
    print(f"median length: ~{catalog_mod.median_tokens(cat)} tokens (placebo target)")
    return 0


def _cmd_design(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.catalog).read_text())
    ids = [s["id"] for s in payload["skills"]]
    if args.stage == "screening":
        matrix = design_mod.screening_design(len(ids), resolution=args.resolution)
    else:
        matrix = design_mod.full_factorial(len(ids))
    configs = design_mod.configurations(matrix, ids)
    out = Path(args.out)
    out.write_text(
        json.dumps([{"index": c.index, "skills": list(c.skills)} for c in configs], indent=2)
    )
    print(f"{args.stage}: {matrix.shape[0]} configurations over {len(ids)} skills -> {out}")
    return 0


def _cmd_estimate(args: argparse.Namespace) -> int:
    records = ledger_mod.load(args.ledger)
    report_mod.guard([r.harness for r in records])
    tasks = sorted({r.task_id for r in records})
    players = sorted({s for r in records for s in r.skills_assigned})
    values = ledger_mod.value_table(records, tasks, outcome=args.outcome)
    phi = estimate_mod.shapley_exact_by_task(values, players)
    intervals = estimate_mod.bootstrap_ci(phi, players, seed=args.seed)
    residual = estimate_mod.efficiency_residual(phi, values, players)
    text = report_mod.report_card(
        records[0].catalog_source, records[0].catalog_commit, intervals, residual
    )
    Path(args.out).write_text(text)
    print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="psa", description="Principal Skill Analysis")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("catalog", help="discover and pin a skill catalog")
    c.add_argument("path")
    c.add_argument("--out", default="results/catalog.json")
    c.set_defaults(func=_cmd_catalog)

    d = sub.add_parser("design", help="emit the run matrix")
    d.add_argument("catalog")
    d.add_argument("--stage", choices=["screening", "exact"], default="screening")
    d.add_argument("--resolution", type=int, default=4)
    d.add_argument("--out", default="results/design.json")
    d.set_defaults(func=_cmd_design)

    e = sub.add_parser("estimate", help="compute attributions from a ledger")
    e.add_argument("ledger")
    e.add_argument("--outcome", default="resolved")
    e.add_argument("--seed", type=int, default=0)
    e.add_argument("--out", default="results/report.md")
    e.set_defaults(func=_cmd_estimate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
