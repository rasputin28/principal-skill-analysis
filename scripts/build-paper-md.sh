#!/usr/bin/env bash
# Regenerate the readable mirror paper.md from the canonical paper/main.tex.
# Run after editing the LaTeX; CI fails if the two are out of sync.
set -euo pipefail
cd "$(dirname "$0")/.."

# pandoc's markdown output is not stable across versions; the CI sync check pins
# the same one. If you bump this, bump PANDOC_VERSION in .github/workflows/paper.yml.
PANDOC_VERSION="3.10"
have=$(pandoc --version | head -1 | awk '{print $2}')
if [ "$have" != "$PANDOC_VERSION" ]; then
  echo "warning: pandoc $have, expected $PANDOC_VERSION; regenerated output may differ from CI" >&2
fi

{
  cat <<'HDR'
<!-- Generated from paper/main.tex by scripts/build-paper-md.sh. Do not edit by hand. -->

> **This is a readable mirror.** The canonical source is
> [`paper/main.tex`](paper/main.tex), which is what gets submitted; the compiled PDF is a build
> artifact of the `paper` workflow. Edit the LaTeX, then run `scripts/build-paper-md.sh`.

HDR
  pandoc paper/main.tex -f latex -t gfm --wrap=preserve
} > paper.md

echo "paper.md regenerated ($(wc -w < paper.md) words)"
