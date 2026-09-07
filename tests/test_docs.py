"""The documentation carries real mathematics, so it is checked like code.

GitHub renders LaTeX in Markdown, which means a malformed expression fails
silently: the reader sees raw backslashes rather than an error. These tests
catch the three ways that happens.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = [
    ROOT / "README.md",
    ROOT / "METHODOLOGY.md",
    ROOT / "docs/superpowers/specs/2026-09-06-psa-design.md",
]

# Commands KaTeX renders, which is what GitHub uses. A command outside this set
# is not necessarily wrong, but it has not been checked, so it is flagged.
KATEX = {
    "Big", "Bigg", "Longrightarrow", "Rightarrow", "approx", "bar", "big", "bigg",
    "binom", "cdot", "cdots", "cup", "cap", "dots", "emptyset", "frac", "ge", "in",
    "langle", "lceil", "le", "left", "leq", "mathbb", "mathbf", "mathrm", "neq",
    "ni", "notin", "operatorname", "qquad", "quad", "rangle", "rceil", "right",
    "setminus", "subseteq", "sum", "text", "times", "triangle", "underbrace",
    "varphi", "vert", "prod", "int", "sqrt", "alpha", "beta", "phi", "pi", "sigma",
    "theta", "lambda", "mu", "epsilon", "Delta", "Sigma", "infty", "pm", "cong",
}


def _outside_fences(path: Path):
    fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("```"):
            fence = not fence
            continue
        if not fence:
            yield number, line


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: p.name)
def test_inline_math_delimiters_are_balanced(doc):
    """An odd number of dollar signs on a line silently swallows the rest of it."""
    offenders = [
        (n, l) for n, l in _outside_fences(doc)
        if len(re.findall(r"(?<!\\)\$", l)) % 2
    ]
    assert not offenders, "unbalanced $ on: " + "; ".join(f"{n}: {l[:60]}" for n, l in offenders)


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: p.name)
def test_no_absolute_value_bars_inside_table_math(doc):
    """A | inside math in a table row is read as a cell boundary and breaks the table."""
    offenders = []
    for n, line in _outside_fences(doc):
        if not line.lstrip().startswith("|"):
            continue
        for expr in re.findall(r"(?<!\\)\$([^$]*)(?<!\\)\$", line):
            if "|" in expr:
                offenders.append((n, expr))
    assert not offenders, "pipe inside table math: " + "; ".join(f"{n}: {e[:40]}" for n, e in offenders)


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: p.name)
def test_math_fences_are_closed(doc):
    text = doc.read_text(encoding="utf-8")
    assert text.count("```") % 2 == 0, "an unclosed fence swallows the rest of the document"
    assert "```math" in text or doc.name.endswith("design.md"), "expected at least one math block"


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: p.name)
def test_only_commands_known_to_render_are_used(doc):
    used = set(re.findall(r"\\([A-Za-z]+)", doc.read_text(encoding="utf-8")))
    unknown = sorted(used - KATEX)
    assert not unknown, f"unverified LaTeX commands: {unknown}. Confirm KaTeX supports them, then add to KATEX."
