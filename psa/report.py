"""Reporting.

Rule of the house: a report states what its data supports and says so plainly
where it does not. A failed control is printed, not omitted.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .estimate import Interval, LatentAxes


class UnpublishableLedger(Exception):
    """Raised when a ledger must not be turned into a result."""


def guard(harnesses: Sequence[str]) -> None:
    if any(h == "stub" for h in harnesses):
        raise UnpublishableLedger(
            "this ledger contains StubRunner records; its numbers are hashes, "
            "not measurements, and must not be reported"
        )


def controls_verdict(
    placebo: Interval | None,
    saboteur: Interval | None,
) -> tuple[bool, list[str]]:
    """Criteria 1 and 2 of the design document, checked before anything else."""
    notes: list[str] = []
    ok = True
    if placebo is None:
        ok = False
        notes.append("no placebo skill in this run set; attribution is not calibrated")
    elif placebo.excludes_zero:
        ok = False
        notes.append(
            f"NEGATIVE CONTROL FAILED: placebo phi = {placebo.point:+.4f} "
            f"[{placebo.low:+.4f}, {placebo.high:+.4f}] excludes zero. "
            "The instrument is measuring prompt length, not skills."
        )
    else:
        notes.append(
            f"negative control passed: placebo phi = {placebo.point:+.4f} "
            f"[{placebo.low:+.4f}, {placebo.high:+.4f}]"
        )
    if saboteur is None:
        notes.append("no saboteur skill in this run set; positive control not checked")
    elif not (saboteur.excludes_zero and saboteur.point < 0):
        ok = False
        notes.append(
            f"POSITIVE CONTROL FAILED: saboteur phi = {saboteur.point:+.4f} "
            f"[{saboteur.low:+.4f}, {saboteur.high:+.4f}] is not clearly negative."
        )
    else:
        notes.append(f"positive control passed: saboteur phi = {saboteur.point:+.4f}")
    return ok, notes


def report_card(
    catalog_source: str,
    catalog_commit: str,
    intervals: Mapping[str, Interval],
    residual: float,
    axes: LatentAxes | None = None,
    control_notes: Sequence[str] = (),
    controls_ok: bool = True,
) -> str:
    lines = [
        f"# PSA report card",
        "",
        f"- catalog: `{catalog_source}`",
        f"- commit: `{catalog_commit}`",
        f"- efficiency residual: {residual:.2e} (must be ~0)",
        "",
        "## Controls",
        "",
    ]
    lines += [f"- {n}" for n in control_notes] or ["- none recorded"]
    if not controls_ok:
        lines += [
            "",
            "**Controls failed. The attributions below are not reportable and are shown "
            "only for debugging.**",
        ]
    lines += ["", "## Attribution", "", "| skill | phi | 95% CI | distinguishable from zero |", "|---|---|---|---|"]
    for skill, iv in sorted(intervals.items(), key=lambda kv: -abs(kv[1].point)):
        lines.append(
            f"| `{skill}` | {iv.point:+.4f} | [{iv.low:+.4f}, {iv.high:+.4f}] | "
            f"{'yes' if iv.excludes_zero else 'no'} |"
        )
    total = sum(iv.point for iv in intervals.values())
    null_mass = sum(1 for iv in intervals.values() if not iv.excludes_zero)
    lines += [
        "",
        f"Total lift attributed: {total:+.4f}. "
        f"Skills indistinguishable from zero: {null_mass}/{len(intervals)}.",
    ]
    if axes is not None:
        lines += ["", "## Latent axes", "", "| axis | variance explained | top skills |", "|---|---|---|"]
        for j, ratio in enumerate(axes.explained_variance_ratio):
            order = sorted(
                range(len(axes.skills)),
                key=lambda i: -abs(axes.skill_loadings[i, j]),
            )[:3]
            top = ", ".join(
                f"{axes.skills[i]} ({axes.skill_loadings[i, j]:+.2f})" for i in order
            )
            lines.append(f"| {j + 1} | {ratio:.1%} | {top} |")
    return "\n".join(lines) + "\n"
