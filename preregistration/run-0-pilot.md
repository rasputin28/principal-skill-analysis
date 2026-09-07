# PSA pre-registration — run-0-pilot

Committed and hashed **before** the first measurement run of this set. The hash of this file is
cited in any report derived from it. Every field must be filled; a blank field is a degree of
freedom, and a degree of freedom left open is the mechanism this document exists to close.

**Status:** DRAFT — 4 fields marked `[PENDIENTE HUMANO]` must be decided and this file
recommitted before any first run. The file is committed now to establish provenance of the
decisions already made.

---

## 1. Catalogs under test

| role | repository | commit | skills |
|---|---|---|---|
| primary | `obra/superpowers` | pinned at first run | 14 |
| comparison | `addyosmani/agent-skills` | pinned at first run | 25 |

Union catalog: 39 skills before deduplication. Namespaced by catalog to treat collisions as a
finding. Selection rule documented in `preregistration/catalog-selection.md` (2026-09-06).

Controls injected into every configuration: `psa-placebo` (length-matched to the union catalog's
median, exact token count TBD after pilot), `psa-saboteur`.

## 2. Benchmark

- Source: SWE-bench Verified (public split; full list at `swebench.com`).
- Task subset and how it was selected: informative-band filter — keep tasks whose baseline resolve
  rate falls strictly between the lower and upper band bounds below. Applied to the **empty-skill
  baseline** (zero-configuration run). Full excluded task list at
  `preregistration/run-0-pilot-excluded.txt` (written during pilot setup, before any skill run).
- Informative-band criterion (baseline resolve rate must fall within): **[PENDIENTE HUMANO: decide
  lower and upper thresholds before pilot run. Suggested starting point: 0.10–0.90, but must be
  fixed here, not chosen after seeing the baseline distribution.]**
- Tasks excluded by that criterion: listed in full at `preregistration/run-0-pilot-excluded.txt`
  (file created during baseline setup, not yet committed because the band is not yet defined).
- Post-cutoff validation set: PRs merged to `obra/superpowers` and `addyosmani/agent-skills` after
  this document's commit date, applied to SWE-bench repos post-dating this commit. Serves as
  contamination control; not used for primary analysis.

## 3. Execution

- Harness: `ClaudeCodeRunner` (`psa/runner/claude_code.py`), version pinned at this commit.
- Model: **[PENDIENTE HUMANO: specify exact model identifier, e.g. `claude-sonnet-5-20251001`.]**
- Seeds: **[PENDIENTE HUMANO: list the seeds to be used, e.g. `[0, 1, 2]`. Fixed here so that
  seeds cannot be chosen after inspecting results.]**
- Repetitions per (task, configuration) cell: **[PENDIENTE HUMANO: specify, e.g. 3. Determines
  statistical power and total budget. Must be fixed before any run.]**
- Total configurations:
  - Pilot: 2 (empty baseline + full catalog)
  - Screening: 48 (Plackett–Burman Res-IV + foldover, accommodates N≤23 skills after any
    deduplication; 24-run PB folded to 48)
  - Exact: 2^k (k TBD from screening; see Section 4)
  - Validation: budget TBD
- Total runs: `[TBD] = configurations × tasks × repetitions`

## 4. Analysis

- Primary outcome: Shapley value φᵢ for each skill i, computed via the exact Möbius transform
  (screening stage) and the full exact algorithm (exact stage). Implemented in
  `psa/estimate.py::shapley_exact_by_task`.
- Secondary outcomes: interaction index I(i,j) for all pairs among the k retained skills;
  latent task-demand axes (PCA on the task×configuration result matrix); ITT vs. treated gap
  per skill.
- `k`, the number of skills retained after screening (**fixed here, not chosen after seeing the
  estimates**): **[PENDIENTE HUMANO: specify k before running the screening stage. The exact stage
  is 2^k runs; k=7 → 128 configs, k=8 → 256. Must reflect budget and statistical power together.]**
- Screening retention rule: retain the top-k skills by |φᵢ| from the screening stage. Ties
  broken by alphabetical order of skill ID to remove ambiguity.
- Confidence intervals: percentile bootstrap over tasks, 2000 resamples, alpha = 0.05.
- Stability threshold for criterion 3 (Kendall tau between two independent replications): τ ≥ 0.70.

## 5. Hypotheses

The following restate H1–H5 from `paper.md`, bound to the thresholds this run set uses.

- **H1 (global lift):** φ_total = v(S) − v(∅) > 0, where S is the full catalog and v(∅) is
  the baseline. Criterion: φ_total is positive and its 95% CI excludes zero.
- **H2 (concentration):** the top-3 skills by |φᵢ| account for ≥ 50% of φ_total in absolute value.
  Criterion: checked on the exact-stage estimates.
- **H3 (skill interactions):** a majority of all pairwise interaction indices I(i,j) among the k
  retained skills are negative (redundancy dominates over synergy). Criterion: >50% of the
  k(k−1)/2 pairs have I(i,j) < 0.
- **H4 (latent task axes):** the first two PCA components of the task×configuration matrix
  explain ≥ 60% of variance. Criterion: checked on the exact-stage result matrix.
- **H5 (catalog comparison):** mean |φᵢ| for obra/superpowers skills ≠ mean |φᵢ| for
  addyosmani/agent-skills; direction not predicted. Criterion: 95% CI of the difference excludes
  zero.

## 6. Stopping and reporting rules

- The run set stops when: all planned configurations and tasks have been completed, or when budget
  is exhausted (to be declared before the first run alongside repetition count).
- If the negative control (placebo) fails — φ_placebo 95% CI excludes zero — this run set reports:
  **nothing**. The instrument is declared miscalibrated. Analysis is not modified to rescue it.
- If no attribution is distinguishable from zero, that null result is reported as the finding and
  the design is not modified to look again.
- Any deviation from this document is recorded in `preregistration/run-0-pilot-deviations.md` with
  its reason and its date, and is reported alongside the results.
