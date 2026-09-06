# PSA methodology

The exact procedure, stated unambiguously. If something here contradicts `paper.md`, this file is
wrong and should be fixed; the paper is the argument, this is the specification.

---

## 1. The unit of execution is a configuration, not a pair

A **run** is one agent attempt at one benchmark task with one **configuration** loaded.

A configuration `C` is any subset of the catalog `S`. It may contain zero skills, one, five,
seventeen, or all of them. **Nothing in PSA is executed "in pairs."** Pairs — and triples, and
groups of any size — are objects computed *from* the runs during analysis. Confusing the two is
the most natural misreading of this design, so it is stated first.

Concretely, at a catalog of 39 skills:

| stage | configurations run | typical size of a configuration |
|---|---|---|
| pilot | 2 (empty, and the full catalog) | 0 and 39 |
| screening | 80 | about half the catalog, by construction |
| exact | 2^k, e.g. 128 at k=7 | every size from 0 to k |
| validation | budgeted, e.g. 40 | varies along random permutations |

A screening run therefore loads roughly twenty skills at once. That is deliberate: a balanced
design is what allows every skill's effect to be estimated from the same runs, instead of
spending a run per skill.

## 2. The unit of analysis is the within-task difference

Every comparison holds the task, the seed, the model and the harness fixed and varies only the
configuration. All estimates are computed on within-task differences, and all confidence
intervals are bootstrapped over **tasks**, never over runs.

This is what makes the design affordable. Task difficulty is the dominant variance component on
repository-issue benchmarks; blocking on it removes that variance rather than paying to average
it away.

## 3. Stages, and what each one can and cannot answer

### 3.1 Pilot

Runs the empty configuration and the full catalog over a task sample. Produces: the baseline
resolve rate per task, the per-task variance, the informative band, and the invocation record
(which skills ever fired). Answers **H4** (the availability-versus-invocation gap) on its own.
Cannot answer anything about attribution.

### 3.2 Screening — Resolution IV fractional factorial

A Plackett–Burman design followed by its foldover. Runs required as a function of catalog size,
computed by `psa.design.screening_design` rather than quoted from a table:

| skills (N) | Resolution III | **Resolution IV (used)** | full factorial `2^N` |
|---:|---:|---:|---:|
| 5 | 8 | **16** | 32 |
| 10 | 12 | **24** | 1,024 |
| 14 | 16 | **32** | 16,384 |
| 20 | 24 | **48** | 1,048,576 |
| 25 | 32 | **64** | 33,554,432 |
| 30 | 32 | **64** | 1,073,741,824 |
| 39 | 40 | **80** | 549,755,813,888 |
| 41 | 44 | **88** | 2,199,023,255,552 |
| 50 | 60 | **120** | 1,125,899,906,842,624 |

The count grows roughly linearly in `N` while the subset space grows exponentially. This is the
entire reason a catalog of forty skills is measurable at all.

**What screening answers:** the main effect of every skill in the catalog — which skills matter.
**What screening cannot answer:** which specific pair or group is responsible. Resolution IV
separates main effects from two-factor interactions but leaves two-factor interactions aliased
with one another. Separating those requires Resolution V, at a cost that rises steeply with `N`.

**What screening nevertheless guarantees**, and the reason Resolution III is rejected: a skill
whose entire value is combinatorial is *not* discarded here. In a balanced design its partner is
present in half the runs, so a pure pairwise effect still shifts that skill's marginal mean. It
survives to the stage that can identify it. `tests/test_estimate.py::test_pure_interaction_is_
split_evenly_and_ablation_would_miss_it` and `tests/test_design.py::test_foldover_actually_buys_
resolution_iv` assert the two halves of this claim.

### 3.3 Exact — full factorial over the survivors

**Why `2^k`, and what the `2` is.** The `2` is not "pairs". It is the switch: each skill is either
loaded or not loaded, two states, so `k` skills give `2 x 2 x ... x 2 = 2^k` distinct
configurations. And `k` is *not* the size of the harness — `N` is. `k` is what survives screening.

The `2^k` configurations contain every group size at once, in the proportions of a row of
Pascal's triangle. At `k = 7`:

| configuration size | how many | |
|---:|---:|---|
| 0 | 1 | the empty baseline |
| 1 | 7 | skills alone |
| 2 | **21** | **pairs** |
| 3 | 35 | triples |
| 4 | 35 | quadruples |
| 5 | 21 | quintuples |
| 6 | 7 | sextuples |
| 7 | 1 | the whole surviving catalog |
| | **128** | `= 2^7` |

Pairs are 21 of 128 — sixteen per cent of the runs. The design is not "pairwise"; pairs are simply
one of the sizes it covers, and the reason every interaction order is recoverable is that every
size is present.

Every one of the `2^k` subsets of the `k` retained skills is run. Because the subset space is
complete, **every interaction of every order is present in the data exactly**, with no model, no
sampling and no extrapolation. `k` is capped by budget and fixed in the pre-registration before
the screening estimates are seen.

### 3.4 Validation

Permutation sampling over the complete catalog at reduced budget, to check that screening
discarded nothing large. A discarded skill appearing with a large attribution is reported as a
failure of the screening design, not corrected in silence.

## 4. What is computed, at which order

| order | quantity | function | available from |
|---|---|---|---|
| 1 | Shapley value `φᵢ` — what a skill is worth on average | `shapley_exact_by_task` | exact stage |
| 1 | main effect — which skills matter at all | `design.main_effects` | screening |
| 2 | interaction index `I(i,j)` — does this pair help or duplicate | `interaction_index_by_task` | exact stage |
| any | interaction index of a named group | `interaction_index` | exact stage |
| group | orthogonal redundancy areas | `redundancy_axes` | exact stage |
| group | minimal spanning subset | `minimal_spanning_subset` | exact stage |
| any | best measured coalition of a given size | `best_coalitions` | exact stage |
| any | value of the best coalition at every size | `coalition_curve` | exact stage |
| any | is this combination better than that one | `compare_coalitions` | exact stage |
| — | latent axes of task demand | `latent_axes` | screening (coarse, whole catalog) |

`interaction_index` at order 1 reproduces the Shapley value exactly, and at order 2 reproduces
the pairwise index exactly. Both identities are asserted in the test suite, so the three are one
estimator rather than three that happen to agree.

## 5. Catalogs of four, five, or many more skills

The question "which four should I load" is not answered by any per-skill ranking, and it is not
answered by enumerating groups either: reporting the interaction index of every subset would
produce `2^k` numbers, which is a matrix, not a finding. PSA answers it three ways, each sized
to a different decision.

1. **`coalition_curve`** — the value of the *best* coalition at every size, read straight off the
   exact stage. Where the curve flattens is where a context budget should stop. This is the
   primary answer for "how many skills should I load, and which".
2. **`redundancy_axes` and `minimal_spanning_subset`** — the interaction matrix is symmetric, so
   its eigendecomposition collapses arbitrarily large redundancy blocks into single orthogonal
   axes. A group of `m` mutually redundant skills produces *one* eigenvalue, not `m(m-1)/2`
   pairwise numbers. Keeping the best-attributed representative of each area gives the subset
   that reproduces the catalog's coverage at a fraction of its context cost.
3. **`interaction_index(values, players, group)`** — for a specific group you already suspect,
   the exact index at that order, without enumerating every group of that size.

### Reading the additivity gap

`coalition_curve` reports `best_value − additive_prediction` at each size. The gap is identically
zero at size 0 and at the full catalog, by the efficiency property — the attributions are built
to sum to the total lift, so no gap can exist at either end. The information is in between:

- **positive gap** → *redundancy*. Shapley splits credit among substitutes, so any one of a
  redundant group beats its own share, and a small subset buys most of the catalog.
- **negative gap** → *complementarity*. Those skills only pay off alongside partners absent from
  the set; the group must be loaded together or not at all.

## 6. Controls, run before anything of interest

1. **Length-matched placebo** — must have a confidence interval containing zero. If it does not,
   the run set reports nothing.
2. **Saboteur** — must come out significantly negative.
3. **Availability versus invocation** — every attribution is reported twice, intention-to-treat
   and effect-among-invoked.
4. **Contamination** — the attribution ordering is re-checked on post-cutoff tasks.

## 7. Outcomes

Two co-primary outcomes: tasks resolved, and tasks resolved per dollar. Every attribution is
computed against both, and a skill whose sign differs between them is reported as such rather
than resolved in favour of the flattering reading. Secondary: fraction of fail-to-pass tests
satisfied, turns to solution, tokens consumed, whether the patch touched the reference files.

## 8. What PSA does not do

- It does not run pairs, or any fixed group size, as an experimental unit.
- It does not identify specific pairs from the screening stage; that requires the exact stage.
- It does not report the interaction index of every subset; that is `2^k` numbers and no decision.
- It does not measure whether a skill is well written, only whether its presence changed outcomes.
- It does not extrapolate. Every coalition it names was actually run.
