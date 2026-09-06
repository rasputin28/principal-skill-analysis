# Submission source

`main.tex` is the canonical source for the paper. `../paper.md` is a readable mirror for GitHub
and is not what gets submitted.

## Building

No local TeX installation is required: the `paper` workflow compiles `main.tex` on every push
that touches this directory and attaches `main.pdf` as a build artifact. It fails the build on
any undefined reference or citation, so a broken cross-reference cannot reach a submission.

Locally, with a TeX Live installation:

```bash
cd paper && latexmk -pdf main.tex
```

## Submitting to arXiv

arXiv prefers LaTeX source over a finished PDF; source submissions get full-text search and an
HTML rendering, PDF-only submissions get neither. Three properties of this file exist for that
reason and should be preserved:

- **The bibliography is embedded** in a `thebibliography` environment. arXiv does not run BibTeX,
  so a `.bib` file would require shipping a generated `.bbl` alongside it. Embedding avoids the
  whole class of problem.
- **The figure is drawn in TikZ**, not included as an image. arXiv does not accept SVG, and TikZ
  compiles from the same source with no external asset to lose.
- **`\pdfoutput=1`** is set on the second line, which tells arXiv to use pdfLaTeX.

Upload `main.tex` on its own. There is nothing else to include.

Primary classification `cs.SE`; cross-list `cs.LG` and `stat.ME`. Licence CC BY 4.0, matching the
repository.
