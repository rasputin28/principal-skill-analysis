"""Configuration compilation.

Materializes a workspace containing exactly the skills of a configuration and
nothing else. This is where contamination between runs would enter, so the
hermeticity check is part of the module rather than a convention.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path

from .catalog import Catalog


def compile_workspace(
    catalog: Catalog,
    skills: Iterable[str],
    destination: str | Path,
) -> Path:
    """Copy the selected skills into a fresh workspace and return its path."""
    wanted = set(skills)
    unknown = wanted - set(catalog.ids)
    if unknown:
        raise ValueError(f"not in catalog: {sorted(unknown)}")
    destination = Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    source_root = Path(catalog.source)
    for skill in catalog.skills:
        if skill.id not in wanted:
            continue
        src = (source_root / skill.path).parent
        shutil.copytree(src, destination / skill.id)
    return destination


def assert_hermetic(catalog: Catalog, skills: Iterable[str], workspace: str | Path) -> None:
    """Fail if the workspace contains any skill outside the configuration.

    A silent leak here would make every attribution in the study wrong in a way
    no downstream check could detect, so it is asserted rather than assumed.
    """
    wanted = set(skills)
    present = {p.name for p in Path(workspace).iterdir() if p.is_dir()}
    leaked = present - wanted
    if leaked:
        raise AssertionError(f"workspace leaked skills outside the configuration: {sorted(leaked)}")
    absent = wanted - present
    if absent:
        raise AssertionError(f"workspace is missing assigned skills: {sorted(absent)}")
