"""The harness boundary.

Comparing one author's harness against another's requires that the harness be
substitutable. Every supported harness is an implementation of ``Runner``. An
unsupported harness is declared unsupported; it is never approximated.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class RunOutcome:
    resolved: bool
    f2p_fraction: float
    turns: int
    tokens: int
    wall_seconds: float
    skills_invoked: tuple[str, ...]
    notes: dict = field(default_factory=dict)


@runtime_checkable
class Runner(Protocol):
    """Execute one agent run and report what happened, including invocation."""

    name: str
    model: str

    def run(
        self,
        task_id: str,
        workspace: Path,
        skills_assigned: Sequence[str],
        seed: int,
    ) -> RunOutcome: ...


class StubRunner:
    """A deterministic fake for wiring tests. NEVER a source of results.

    It exists so the design, compilation, ledger and estimation stages can be
    exercised end to end before any budget is spent. Its outputs are a hash,
    not a measurement, and :func:`psa.report` refuses to publish a ledger whose
    harness is this one.
    """

    name = "stub"
    model = "none"

    def run(
        self,
        task_id: str,
        workspace: Path,
        skills_assigned: Sequence[str],
        seed: int,
    ) -> RunOutcome:
        digest = hashlib.sha256(
            f"{task_id}|{sorted(skills_assigned)}|{seed}".encode()
        ).digest()
        score = digest[0] / 255.0
        return RunOutcome(
            resolved=score > 0.5,
            f2p_fraction=score,
            turns=1 + digest[1] % 20,
            tokens=1000 + digest[2] * 100,
            wall_seconds=float(digest[3]),
            skills_invoked=tuple(skills_assigned),
            notes={"stub": True},
        )
