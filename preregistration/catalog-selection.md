# Catalog selection

How the catalogs under test were chosen, recorded before measurement so that the selection
itself can be audited. Selection is a researcher degree of freedom like any other.

## Rule, stated before inspecting any catalog's contents

A catalog is eligible if it (a) is a public repository whose skills are discoverable as
`SKILL.md` files, (b) carries a license permitting redistribution, (c) has been updated within
the last month, (d) contains a number of skills the two-stage design can accommodate without a
researcher-chosen subset, and (e) is published under a named author or organization. Among
eligible catalogs, the two with the most GitHub stars are selected.

Criterion (d) is the binding one and the reason the largest catalogs are excluded. A catalog of
several hundred skills cannot be screened without someone choosing which subset to test, and
that choice would be mine.

## Search, 2026-09-06

`gh search repos --topic=claude-code --sort=stars` and `gh search repos "claude skills"`, with
star counts and skill counts verified through the GitHub API rather than the search index.

| repository | stars | SKILL.md | license | pushed | eligible |
|---|---:|---:|---|---|---|
| `obra/superpowers` | 282,332 | 14 | MIT | 2026-09-04 | yes |
| `affaan-m/ECC` | 250,915 | 898 | MIT | 2026-09-05 | no — (d) |
| `NousResearch/hermes-agent` | 242,412 | 198 | MIT | 2026-09-06 | no — (d) |
| `anthropics/skills` | 174,824 | 20 | none | 2026-09-03 | no — (b), first-party |
| `DietrichGebert/ponytail` | 129,025 | 12 | — | — | eligible, ranked below |
| `addyosmani/agent-skills` | 92,553 | 25 | MIT | 2026-09-06 | yes |

## Selected

- **`obra/superpowers`** — 14 skills. Jesse Vincent.
- **`addyosmani/agent-skills`** — 25 skills. Addy Osmani, formerly Director at Google working on
  Gemini and Google Cloud.

Both are MIT, both were updated within days of selection, both fall inside the design's range,
and both are published under a named author with a public engineering record. Together they are
the two most-starred eligible catalogs.

## Declared conflict of interest

`obra/superpowers` is the skill collection the author of this study uses in daily work. It is
included because excluding the most-starred eligible catalog would be a larger distortion than
including it, but the reader should know, and the incumbent should be the harder case to
confirm rather than the easier one.

## Union catalog

The primary measurement is over the **union** of the two catalogs (39 skills before deduplication)
rather than over each separately. This costs fewer screening runs than two independent screens,
and it answers the question the separate screens cannot: when two authors publish a skill for the
same purpose, the Shapley symmetry property splits the credit between them, which is what surfaces
redundancy across the ecosystem instead of hiding it inside one catalog's total.

Skill identifiers are namespaced by catalog, since collisions between catalogs are expected and
are a finding rather than an error.
