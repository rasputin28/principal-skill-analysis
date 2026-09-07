"""Claude Code harness for PSA.

Runs the Claude Code CLI on a SWE-bench task with a compiled skill workspace.
Parses the JSON transcript to extract real skills_invoked from Skill tool calls.

Requirements:
  - ``claude`` binary in PATH (Claude Code CLI)
  - Environment: SWE-bench evaluation environment per task
  - ``CLAUDE_SKILLS_DIR`` must be respected by the CLI (otherwise declare unsupported)

If the CLI cannot report skills_invoked from the transcript, raise HarnessUnsupported
rather than returning a silently wrong measurement.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Sequence
from pathlib import Path

from .base import RunOutcome, Runner


class HarnessUnsupported(Exception):
    """Raised when the harness cannot satisfy a required contract.

    Concretely: when the transcript cannot be parsed for skills_invoked
    or when required CLI features are absent. The harness must NOT fabricate
    invocation data — it must raise this instead.
    """


# The env var that tells Claude Code which skills directory to use.
# If the CLI does not honour this, the harness is unsupported.
_SKILLS_DIR_ENV = "CLAUDE_SKILLS_DIR"

# Claude Code CLI output format flag. Requires a version that supports it.
_JSON_FLAG = "--output-format"
_JSON_VALUE = "json"


def _parse_transcript(raw: str) -> tuple[bool, float, int, int, float, tuple[str, ...]]:
    """Parse Claude Code JSON output into run metrics.

    Returns (resolved, f2p_fraction, turns, tokens, wall_seconds, skills_invoked).
    Raises HarnessUnsupported if the transcript cannot be parsed.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HarnessUnsupported(
            f"claude output was not valid JSON: {exc}. "
            "Run `claude --version` to confirm the CLI is installed."
        ) from exc

    # SWE-bench result fields expected from the CLI
    try:
        resolved: bool = bool(data["result"]["resolved"])
        f2p: float = float(data["result"].get("f2p_fraction", float(resolved)))
        turns: int = int(data.get("turns", 1))
        tokens: int = int(data.get("usage", {}).get("total_tokens", 0))
    except (KeyError, TypeError, ValueError) as exc:
        raise HarnessUnsupported(
            f"transcript missing required fields: {exc}. "
            "Expected keys: result.resolved, turns, usage.total_tokens."
        ) from exc

    # Extract which skills were actually invoked via Skill tool calls.
    # A Skill tool call looks like: {"type":"tool_use","name":"Skill","input":{"skill":"..."}}
    # We require this to be parseable; ambiguity → HarnessUnsupported.
    messages = data.get("messages", [])
    if not isinstance(messages, list):
        raise HarnessUnsupported("transcript 'messages' is not a list; cannot parse invocations")

    skill_calls: list[str] = []
    for msg in messages:
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") == "Skill"
            ):
                skill_id = block.get("input", {}).get("skill")
                if skill_id:
                    skill_calls.append(skill_id)

    # If the messages key was present but empty, we accept zero invocations as valid.
    # If the key was absent entirely, we cannot distinguish "no invocations" from
    # "invocation data not captured" — so we declare unsupported.
    if "messages" not in data:
        raise HarnessUnsupported(
            "transcript has no 'messages' key; cannot determine which skills were invoked. "
            "The PSA design requires skills_invoked, not just skills_assigned."
        )

    return resolved, f2p, turns, tokens, 0.0, tuple(dict.fromkeys(skill_calls))


class ClaudeCodeRunner:
    """Production runner using the Claude Code CLI.

    Parameters
    ----------
    model:
        Model identifier passed to ``claude --model``.
    timeout:
        Maximum wall seconds per run. Default 30 minutes.
    extra_env:
        Additional environment variables for the subprocess.
    """

    name = "claude-code"

    def __init__(
        self,
        model: str,
        timeout: int = 1800,
        extra_env: dict[str, str] | None = None,
    ) -> None:
        self.model = model
        self.timeout = timeout
        self._extra_env = extra_env or {}

    def run(
        self,
        task_id: str,
        workspace: Path,
        skills_assigned: Sequence[str],
        seed: int,
    ) -> RunOutcome:
        """Execute one agent run and return the outcome.

        Parameters
        ----------
        task_id:
            SWE-bench task identifier.
        workspace:
            Hermetic directory containing exactly the skills for this configuration.
        skills_assigned:
            The skill IDs included in this configuration (used for bookkeeping).
        seed:
            Random seed passed to the CLI for reproducibility.
        """
        workspace = Path(workspace)
        env = {**os.environ, **self._extra_env, _SKILLS_DIR_ENV: str(workspace)}

        cmd = [
            "claude",
            _JSON_FLAG, _JSON_VALUE,
            "--model", self.model,
            "--seed", str(seed),
            "--task", task_id,
        ]

        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except FileNotFoundError as exc:
            raise HarnessUnsupported(
                "claude binary not found in PATH. "
                "Install the Claude Code CLI before running PSA."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise HarnessUnsupported(
                f"run exceeded timeout ({self.timeout}s) for task {task_id!r}"
            ) from exc
        wall = time.monotonic() - t0

        if proc.returncode != 0:
            raise HarnessUnsupported(
                f"claude exited with code {proc.returncode} for task {task_id!r}.\n"
                f"stderr: {proc.stderr[:500]}"
            )

        resolved, f2p, turns, tokens, _, skills_invoked = _parse_transcript(proc.stdout)

        return RunOutcome(
            resolved=resolved,
            f2p_fraction=f2p,
            turns=turns,
            tokens=tokens,
            wall_seconds=wall,
            skills_invoked=skills_invoked,
            notes={"harness": self.name, "task_id": task_id},
        )
