"""Catalog normalization.

The catalog under test is an input to PSA, identified by repository and
commit. This module discovers the skills it contains and records their
provenance so that a measurement can be tied to an exact revision.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

SKILL_FILENAMES = ("SKILL.md", "skill.md")


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    description: str
    path: str
    chars: int
    approx_tokens: int


@dataclass(frozen=True)
class Catalog:
    source: str
    commit: str
    skills: tuple[Skill, ...]

    @property
    def ids(self) -> list[str]:
        return [s.id for s in self.skills]

    def to_json(self, path: Path) -> None:
        payload = {
            "source": self.source,
            "commit": self.commit,
            "skills": [asdict(s) for s in self.skills],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def _frontmatter(text: str) -> dict[str, str]:
    """Parse the leading YAML block. Only flat scalar keys are used."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip().strip("'\"")
    return out


def _commit(root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unversioned"


def discover(root: str | Path) -> Catalog:
    """Find every skill under ``root`` and pin the revision it came from.

    ``approx_tokens`` is a character-count heuristic, not a tokenizer result.
    It exists to size the length-matched placebo of the design document, where
    matching the catalog median within a reasonable margin is what matters.
    """
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    found: list[Skill] = []
    # Case-insensitive filesystems report the same file under every spelling in
    # SKILL_FILENAMES, so paths are deduplicated before they become skills.
    candidates = sorted(
        {
            path.resolve()
            for path in root.rglob("*.md")
            if path.name.lower() in {n.lower() for n in SKILL_FILENAMES}
        }
    )
    for path in candidates:
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = _frontmatter(text)
        rel = path.relative_to(root)
        skill_id = meta.get("name") or rel.parent.name
        found.append(
            Skill(
                id=skill_id,
                name=meta.get("name", skill_id),
                description=meta.get("description", ""),
                path=str(rel),
                chars=len(text),
                approx_tokens=round(len(text) / 4),
            )
        )
    seen: dict[str, Skill] = {}
    for skill in found:
        if skill.id in seen:
            raise ValueError(
                f"duplicate skill id {skill.id!r} at {skill.path} and {seen[skill.id].path}"
            )
        seen[skill.id] = skill
    return Catalog(source=str(root), commit=_commit(root), skills=tuple(found))


def median_tokens(catalog: Catalog) -> int:
    """Median skill length, which the placebo skill must match."""
    sizes = sorted(s.approx_tokens for s in catalog.skills)
    if not sizes:
        raise ValueError("empty catalog")
    mid = len(sizes) // 2
    return sizes[mid] if len(sizes) % 2 else (sizes[mid - 1] + sizes[mid]) // 2
