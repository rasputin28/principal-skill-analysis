"""Tests for the ClaudeCodeRunner harness.

All tests mock subprocess.run — no API calls are made. The point is to verify
the parsing logic, the contracts (HarnessUnsupported), and the subprocess
invocation pattern.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from psa.runner import ClaudeCodeRunner, HarnessUnsupported
from psa.runner.claude_code import _parse_transcript, _SKILLS_DIR_ENV


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_transcript(
    resolved: bool = True,
    f2p: float = 1.0,
    turns: int = 5,
    tokens: int = 3000,
    skill_calls: list[str] | None = None,
    include_messages: bool = True,
) -> str:
    messages = []
    if include_messages:
        for skill_id in (skill_calls or []):
            messages.append({
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Skill",
                        "input": {"skill": skill_id},
                    }
                ],
            })
    data: dict = {
        "result": {"resolved": resolved, "f2p_fraction": f2p},
        "turns": turns,
        "usage": {"total_tokens": tokens},
    }
    if include_messages:
        data["messages"] = messages
    return json.dumps(data)


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "planner" / "SKILL.md").mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def runner():
    return ClaudeCodeRunner(model="claude-sonnet-5", timeout=10)


# ---------------------------------------------------------------------------
# _parse_transcript unit tests
# ---------------------------------------------------------------------------

def test_parse_transcript_basic():
    raw = _make_transcript(resolved=True, f2p=0.8, turns=3, tokens=1200, skill_calls=["planner"])
    resolved, f2p, turns, tokens, wall, skills = _parse_transcript(raw)
    assert resolved is True
    assert f2p == pytest.approx(0.8)
    assert turns == 3
    assert tokens == 1200
    assert skills == ("planner",)


def test_parse_transcript_no_skill_calls():
    raw = _make_transcript(resolved=False, f2p=0.0, skill_calls=[])
    resolved, f2p, turns, tokens, wall, skills = _parse_transcript(raw)
    assert resolved is False
    assert skills == ()


def test_parse_transcript_deduplicates_skills():
    raw = _make_transcript(skill_calls=["planner", "planner", "tester", "planner"])
    *_, skills = _parse_transcript(raw)
    assert skills == ("planner", "tester")


def test_parse_transcript_multiple_skills_preserves_order():
    raw = _make_transcript(skill_calls=["tester", "planner"])
    *_, skills = _parse_transcript(raw)
    assert skills == ("tester", "planner")


def test_parse_transcript_missing_messages_key_raises():
    raw = _make_transcript(include_messages=False)
    with pytest.raises(HarnessUnsupported, match="'messages' key"):
        _parse_transcript(raw)


def test_parse_transcript_invalid_json_raises():
    with pytest.raises(HarnessUnsupported, match="not valid JSON"):
        _parse_transcript("not json at all")


def test_parse_transcript_missing_result_raises():
    raw = json.dumps({"turns": 1, "usage": {"total_tokens": 0}, "messages": []})
    with pytest.raises(HarnessUnsupported, match="missing required fields"):
        _parse_transcript(raw)


def test_parse_transcript_f2p_defaults_to_resolved_when_absent():
    data = {
        "result": {"resolved": True},
        "turns": 1,
        "usage": {"total_tokens": 0},
        "messages": [],
    }
    resolved, f2p, *_ = _parse_transcript(json.dumps(data))
    assert resolved is True
    assert f2p == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# ClaudeCodeRunner integration tests (subprocess mocked)
# ---------------------------------------------------------------------------

def _make_completed_proc(stdout: str, returncode: int = 0):
    proc = MagicMock(spec=subprocess.CompletedProcess)
    proc.stdout = stdout
    proc.stderr = ""
    proc.returncode = returncode
    return proc


def test_runner_sets_skills_dir_env(runner, workspace):
    transcript = _make_transcript(skill_calls=["planner"])
    with patch("subprocess.run", return_value=_make_completed_proc(transcript)) as mock_run:
        runner.run("task-1", workspace, ["planner"], seed=0)
    env_used = mock_run.call_args.kwargs["env"]
    assert env_used[_SKILLS_DIR_ENV] == str(workspace)


def test_runner_passes_model_and_seed(runner, workspace):
    transcript = _make_transcript()
    with patch("subprocess.run", return_value=_make_completed_proc(transcript)) as mock_run:
        runner.run("task-1", workspace, [], seed=42)
    cmd = mock_run.call_args.args[0]
    assert "--model" in cmd
    assert "claude-sonnet-5" in cmd
    assert "--seed" in cmd
    assert "42" in cmd


def test_runner_returns_outcome_with_correct_fields(runner, workspace):
    transcript = _make_transcript(
        resolved=True, f2p=0.75, turns=4, tokens=2000, skill_calls=["tester"]
    )
    with patch("subprocess.run", return_value=_make_completed_proc(transcript)):
        outcome = runner.run("task-1", workspace, ["tester"], seed=0)
    assert outcome.resolved is True
    assert outcome.f2p_fraction == pytest.approx(0.75)
    assert outcome.turns == 4
    assert outcome.tokens == 2000
    assert outcome.skills_invoked == ("tester",)
    assert outcome.wall_seconds >= 0.0


def test_runner_raises_on_nonzero_exit(runner, workspace):
    proc = _make_completed_proc("", returncode=1)
    proc.stderr = "fatal error"
    with patch("subprocess.run", return_value=proc):
        with pytest.raises(HarnessUnsupported, match="exited with code 1"):
            runner.run("task-1", workspace, [], seed=0)


def test_runner_raises_when_binary_missing(runner, workspace):
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(HarnessUnsupported, match="not found in PATH"):
            runner.run("task-1", workspace, [], seed=0)


def test_runner_raises_on_timeout(runner, workspace):
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 10)):
        with pytest.raises(HarnessUnsupported, match="timeout"):
            runner.run("task-1", workspace, [], seed=0)


def test_runner_raises_when_transcript_has_no_messages(runner, workspace):
    transcript = _make_transcript(include_messages=False)
    with patch("subprocess.run", return_value=_make_completed_proc(transcript)):
        with pytest.raises(HarnessUnsupported, match="'messages' key"):
            runner.run("task-1", workspace, [], seed=0)


def test_runner_name_and_model_are_correct(runner):
    assert runner.name == "claude-code"
    assert runner.model == "claude-sonnet-5"


def test_runner_satisfies_runner_protocol():
    from psa.runner import Runner
    assert isinstance(ClaudeCodeRunner(model="claude-sonnet-5"), Runner)


def test_runner_extra_env_is_forwarded(workspace):
    runner = ClaudeCodeRunner(model="claude-sonnet-5", extra_env={"FOO": "bar"})
    transcript = _make_transcript()
    with patch("subprocess.run", return_value=_make_completed_proc(transcript)) as mock_run:
        runner.run("task-1", workspace, [], seed=0)
    env_used = mock_run.call_args.kwargs["env"]
    assert env_used.get("FOO") == "bar"
