# PSA pre-registration — <run name>

Committed and hashed **before** the first measurement run of this set. The hash of this file is
cited in any report derived from it. Every field must be filled; a blank field is a degree of
freedom, and a degree of freedom left open is the mechanism this document exists to close.

## 1. Catalogs under test

| role | repository | commit | skills |
|---|---|---|---|
| primary |  |  |  |
| comparison (optional) |  |  |  |

Controls injected into every configuration: `psa-placebo` (length-matched to the primary
catalog's median, ___ approx. tokens), `psa-saboteur`.

## 2. Benchmark

- Source:
- Task subset and how it was selected:
- Informative-band criterion (baseline resolve rate must fall within): ___ to ___
- Tasks excluded by that criterion (listed in full at `preregistration/<run>-excluded.txt`):
- Post-cutoff validation set (contamination control):

## 3. Execution

- Harness and version:
- Model and version:
- Seeds:
- Repetitions per (task, configuration) cell:
- Total configurations: screening ___ + exact ___ + validation ___
- Total runs: ___ = configurations × tasks × repetitions

## 4. Analysis

- Primary outcome:
- Secondary outcomes:
- `k`, the number of skills retained after screening (**fixed here, not chosen after seeing the
  estimates**):
- Screening retention rule:
- Confidence intervals: percentile bootstrap over tasks, ___ resamples, alpha = ___
- Stability threshold for criterion 3 (Kendall tau between two independent replications):

## 5. Hypotheses

Restate H1–H5 from `paper.md`, or the subset this run set can address, with the specific
numerical thresholds this run will use to judge each one.

## 6. Stopping and reporting rules

- The run set stops when: 
- If the negative control (placebo) fails, this run set reports: **nothing**.
- If no attribution is distinguishable from zero, that null result is reported as the finding and
  the design is not modified to look again.
- Any deviation from this document is recorded in `preregistration/<run>-deviations.md` with its
  reason and its date, and is reported alongside the results.
