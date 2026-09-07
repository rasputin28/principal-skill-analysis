# PSA methodology

The exact procedure, stated unambiguously. If something here contradicts `paper.md`, this file is
wrong and should be fixed; the paper is the argument, this is the specification.

---

## 0. Terms

Every technical word used below, defined once. Nothing here is assumed known.

**Skill** — one written instruction file an agent can load. **Catalogue** — a set of them, pinned
to a repository and revision. **Configuration** — the subset of a catalogue made available for one
attempt at one task; it may be empty, one skill, or all of them. **Run** — one attempt: one agent,
one task, one configuration. **Lift** — $v(S) - v(\emptyset)$: how much better the agent does with the whole catalogue loaded
than with none of it.

**Main effect of a skill** — $\bar v_{j+} - \bar v_{j-}$: the average result across the runs where
skill $j$ was loaded, minus the average across the runs where it was not. It is the crudest possible measure of a skill: what
happens on average when it is present.

**Balanced design** — a layout of runs in which every skill is loaded in half of them. **Orthogonal
columns** — two skills arranged so that all four possibilities (both loaded, either one alone,
neither) occur in a quarter of the runs each, so that neither skill's presence tells you anything
about the other's.

**Aliasing** — two different effects that produce the same pattern across the runs, and therefore
cannot be told apart no matter how much data is collected. It is not a subtlety of interpretation:
it is an identity between two columns of the design. Section 3.2 derives where it comes from.

**Fractional factorial design** — a layout that runs only a fraction of the possible
configurations, chosen so that the effects of interest can still be recovered. **Plackett--Burman
design** — a standard recipe for building such a layout with the balance and orthogonality
properties above. **Foldover** — appending a second copy of a design with every choice reversed,
which doubles the runs and removes a specific kind of aliasing.

**Shapley value** — written $\varphi_i$: the score given to skill $i$ by averaging, over every
combination of the others, how much the result improved at the moment that skill was added. **Dividend of a combination** — written $a(T)$, the part of the worth of $T$ that no smaller
combination accounts for, defined by $a(T) = \sum_{L \subseteq T} (-1)^{|T|-|L|} v(L)$ and satisfying
$v(C) = \sum_{T \subseteq C} a(T)$. A skill's dividend
is what it is worth alone; a pair's dividend is what the pair is worth beyond the two separately.
**Interaction order** — the largest $|T|$ with $a(T) \neq 0$. **Interaction index** — written $I(i,j)$, the same idea applied to a pair: the average of
$v(C \cup \{i,j\}) - v(C \cup \{i\}) - v(C \cup \{j\}) + v(C)$ over contexts $C$, which measures how
much the worth of one skill changes depending on whether the other is loaded. **Eigendecomposition** — rewriting a symmetric table of pairwise numbers as a set of
mutually independent directions, each with a number saying how much of the table it accounts for.

**Bootstrap** — estimating how much a result would move under a different sample by repeatedly
redrawing the sample you have, with replacement, and recomputing.

**Fail-to-pass tests** — in a repository-issue benchmark, the tests that failed before the
reference fix and passed after it. They are what the agent's patch has to satisfy.

**Hermetic workspace** — a working directory containing the files of exactly one configuration and
nothing else, verified rather than assumed.

**Informative band** — the tasks that the baseline agent solves sometimes but not always. Tasks it
always solves and tasks it never solves cannot reveal anything about skills.

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
| exact | $2^k$, e.g. $128$ at $k=7$ | every size from $0$ to $k$ |
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

### 3.2 Primary route — bounded interaction order

Enumeration is hopeless ($2^{39}$), but enumeration is not the only way. Rewrite the value function
in terms of **dividends**: `v(C)` is the sum of the dividends of every combination inside `C`. That
rewriting is exact and unique, and the score of a skill turns out to be the sum of the dividends of
every combination containing it, each split equally among its members.

```math
v(C) \;=\; \sum_{T \subseteq C} a(T)
\qquad\Longrightarrow\qquad
\varphi_i \;=\; \sum_{T \,\ni\, i} \frac{a(T)}{|T|}
```

The consequence is the whole design. **If $a(T) = 0$ for every $|T| > t$, the scores are determined
by $p = \sum_{j=0}^{t} \binom{N}{j} = O(N^{t})$ numbers instead of $2^N$.** At $N = 39$, $t = 2$:

| | count |
|---|---:|
| configurations, if enumerated, $2^{39}$ | $549{,}755{,}813{,}888$ |
| dividends of order $\le 2$, $\;1 + \binom{39}{1} + \binom{39}{2}$ | $\mathbf{781}$ |

Nothing is approximated: inside the assumption the answer is exact. What is paid is the assumption,
and the assumption is **tested, not trusted** (§3.4).

How many runs it takes is a separate question with a proved answer: **a design recovers every
effect up to order $t$ if and only if its resolution is at least $2t+1$.** Measuring every pair
($t = 2$) therefore needs resolution $5$. The design must also have at least $p$ runs, since $781$
unknowns cannot come out of fewer equations.

### 3.3 Fallback route — screening at Resolution IV

Used when the budget will not stretch to $p$ configurations. Cheaper, and weaker in a specific way
that is stated rather than hidden: a skill dropped at screening is dropped for good and the
analysis has no way to notice, which is exactly what the held-out check of §3.4 provides and this
route does not.

**What "Resolution" means, since the table below uses it.** A design that runs only some of the
possible configurations pays for that saving in aliasing: some pairs of effects become
indistinguishable. Resolution names *which* pairs.

| resolution | what is confused with what | consequence here |
|---|---|---|
| **III** | a skill's own effect with the effect of some *pair* of other skills | A skill that only works alongside one other is confounded with an ordinary solo effect, and can cancel to zero. Unusable for this study. |
| **IV** | no skill's own effect with any pair, but pairs with *other pairs* | Every skill's own effect is clean. Pairs are preserved but cannot be told apart from each other yet. **This is what PSA screens with.** |
| **V** | nothing among skills and pairs | Every skill and every pair separately measurable. Correct but far more expensive as the catalogue grows. |

The numeral is the size of the smallest group of effects that gets confused together, so higher is
cleaner and costlier. Section 3.2 of the paper derives all three from the estimator rather than
asserting them.

PSA screens at Resolution IV and pays double the runs of Resolution III for it, because the skills
this study exists to find are exactly the ones Resolution III would lose.

Runs required as a function of catalogue size, computed by `psa.design.screening_design` rather
than quoted from a table:

| skills $N$ | Resolution III | **Resolution IV (used)** | full factorial $2^N$ |
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

### 3.4 Testing the order assumption

The one substantive assumption of the primary route is measured, not asserted.

1. Split the configurations into an estimation set and a held-out set, by a seed fixed in the
   pre-registration.
2. Fit the order-`t` dividends on the estimation set only.
3. Predict the held-out configurations, which the fit never saw.
4. Compare the prediction error against the **noise floor**: the variance between repeated runs of
   the same configuration, which no model can beat.

`fit_bounded_order` refuses outright when the configurations actually run cannot identify the
dividends — too few runs, or the wrong ones. That refusal is the resolution requirement made
concrete rather than a separate check to remember.

If held-out error sits at the floor, the order-`t` description is capturing everything but noise.
If it stands clearly above the floor, interactions above order `t` carry real signal and the
reported scores are incomplete. The threshold is pre-registered, and a failed test is reported as a
failed test rather than met with a larger `t` chosen after the fact.

### 3.5 Exact — full factorial over the survivors

**Why $2^k$, and what the $2$ is.** The $2$ is not "pairs". It is the switch: each skill is either
loaded or not, two states, so $k$ skills give $\underbrace{2 \times 2 \times \cdots \times 2}_{k} = 2^k$
distinct configurations. And $k$ is *not* the size of the harness — $N$ is. $k$ is what survives
screening.

The $2^k$ configurations contain every group size at once, in the proportions $\binom{k}{m}$ of a
row of Pascal's triangle, since $\sum_{m=0}^{k}\binom{k}{m} = 2^k$. At $k = 7$:

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
| | $\mathbf{128}$ | $= 2^7$ |

Pairs are 21 of 128 — sixteen per cent of the runs. The design is not "pairwise"; pairs are simply
one of the sizes it covers, and the reason every interaction order is recoverable is that every
size is present.

Every one of the $2^k$ subsets of the $k$ retained skills is run. Because the subset space is
complete, **every interaction of every order is present in the data exactly**, with no model, no
sampling and no extrapolation. `k` is capped by budget and fixed in the pre-registration before
the screening estimates are seen.

### 3.6 Validation

Permutation sampling over the complete catalog at reduced budget, to check that screening
discarded nothing large. A discarded skill appearing with a large attribution is reported as a
failure of the screening design, not corrected in silence.

## 4. What is computed, at which order

| order | quantity | function | available from |
|---|---|---|---|
| 1 | Shapley value $\varphi_i$ — what a skill is worth on average | `shapley_exact_by_task` | exact stage |
| 1 | main effect — which skills matter at all | `design.main_effects` | screening |
| ≤ t | dividends, exact transform (needs the full lattice) | `estimate.mobius_coefficients` | exact stage |
| ≤ t | dividends fitted from a partial design, by least squares | `estimate.fit_bounded_order` | primary route |
| — | is bounded order actually true here? | `estimate.holdout_faithfulness` | primary route |
| 2 | interaction index $I(i,j)$ — does this pair help or duplicate | `interaction_index_by_task` | exact stage |
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
produce $2^k$ numbers, which is a matrix, not a finding. PSA answers it three ways, each sized
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

`coalition_curve` reports $v(B_m) - \big(v(\emptyset) + \sum_{i \in B_m}\varphi_i\big)$ at each size $m$, where $B_m$ is the best measured coalition of that size. The gap is identically
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
3. **Availability versus invocation** — every attribution is reported twice. Once counting every
   run where the skill was available whether or not the agent used it, which answers "what happens
   if I install this" and is the convention clinical trials call *intention-to-treat*. Once
   counting only the runs where it was actually invoked, which answers "what does it do when
   used".
4. **Contamination** — the attribution ordering is re-checked on post-cutoff tasks.

## 7. Outcomes

Two co-primary outcomes: tasks resolved, and tasks resolved per dollar. Every attribution is
computed against both, and a skill whose sign differs between them is reported as such rather
than resolved in favour of the flattering reading. Secondary: fraction of fail-to-pass tests
satisfied, turns to solution, tokens consumed, whether the patch touched the reference files.

## 8. What PSA does not do

- It does not run pairs, or any fixed group size, as an experimental unit.
- It does not identify specific pairs from the screening stage; that requires the exact stage.
- It does not report the interaction index of every subset; that is $2^k$ numbers and no decision.
- It does not measure whether a skill is well written, only whether its presence changed outcomes.
- It does not extrapolate. Every coalition it names was actually run.
