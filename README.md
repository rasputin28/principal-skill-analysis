# PSA — Principal Skill Analysis

**Which parts of an agent skill collection actually earn their keep, and which are decoration?**

Everyone publishes a harness. Everyone claims it helps. Nobody measures which *parts* of it
help, whether any part is doing nothing, or whether two authors' collections can be compared at
all. That is an empirical question being settled by assertion.

PSA is the instrument for settling it by measurement. You point it at a skill collection — any
repository, any author, pinned to a commit — and it returns the marginal contribution of each
skill with a confidence interval, the contribution of skills *in combination*, and a comparison
against any other collection on a common baseline.

> **Status: pre-registration. No results yet.**
> The methodology, the design generator, the estimator and the controls are implemented and
> tested. No measurement run has been executed. `paper.md` is a Stage 1 Registered Report:
> hypotheses and analysis plan are fixed before data collection, deliberately.

---

## Why not just run an ablation?

Because leave-one-out ablation cannot tell a useless skill from a skill that only works in
company. Remove either one from a full collection and the rest compensates; both read as null.
The distinction matters, because one is safe to drop and the other is not.

PSA estimates each skill's **Shapley value** over the space of skill subsets. The averaging over
coalitions is what recovers combination effects, and the efficiency property guarantees that the
individual contributions sum *exactly* to the collection's total lift — so the ranked bar chart
is a real decomposition, not a normalized ranking that resembles one.

```
φᵢ = Σ_{C ⊆ S\{i}}  [ |C|! (N−|C|−1)! / N! ] · [ v(C ∪ {i}) − v(C) ]
```

## Combinations, not just skills

A per-skill number cannot say whether skill 1 is better paired with skill 3 than with skill 2 —
the Shapley value averages over coalitions and then collapses them. PSA keeps the structure and
reports it:

```python
estimate.interaction_index_by_task(values, skills)   # synergy (+) vs redundancy (-), every pair
estimate.compare_coalitions(values, ["s1","s3"], ["s1","s2"])   # the literal question, with a CI
estimate.best_coalitions(values, size=3)             # given room for three, which three
```

Negative interaction is the expected case and the one nobody reports: two skills that do the
same job, both loaded, spending context to buy what one already bought. Hypothesis H6 says
published catalogs are subadditive for exactly this reason.

### From 741 pairs to a decision

Pairwise numbers do not scale into a decision — 39 skills means 741 pairs. The interaction matrix
is symmetric, so its eigendecomposition gives orthogonal axes in skill space, and the most
negative ones name the areas where a catalog has piled several skills onto one job:

```python
structure = estimate.redundancy_axes(interaction, skills)
estimate.minimal_spanning_subset(structure, phi)   # one per area; the rest is context cost
```

The reading is algebraic, not interpretive: a block of `m` mutually redundant skills interacting
pairwise at `-c` yields an eigenvalue of `-c(m-1)` with a uniform eigenvector over the block, which
is asserted in `tests/test_estimate.py::test_redundancy_axes_recover_a_planted_block`.

Orthogonality here is *imposed by the method, not discovered in the data*. These are the
orthogonal directions that best account for the observed redundancy; they are not evidence that
capabilities are orthogonal.

The exact stage runs every subset of the surviving skills, so all of this comes out of the same
runs at no extra cost. The screening stage deliberately does not identify pairs — Resolution IV
separates main effects from two-factor interactions but leaves those aliased with each other —
and it does not need to, because a skill whose entire value is a pairwise interaction still
shifts the marginal mean in a balanced design and therefore survives to the stage that can
measure it.

## How it stays affordable

The subset space is `2^N`. Two stages plus a validation pass:

| Stage | Design | Configurations at N=20 |
|---|---|---|
| Screening | Resolution IV fractional factorial (Plackett–Burman + foldover) | 48 |
| Exact | Full factorial over the `k` survivors | 128 at `k=7` |
| Validation | Permutation sampling over the whole catalog | budgeted |

Resolution IV, not III: Resolution III aliases main effects with two-factor interactions, and a
two-factor interaction *is* a skill that only works in combination — the phenomenon this tool
exists to detect. Halving the screening budget by aliasing it away would defeat the study.
`tests/test_design.py::test_foldover_actually_buys_resolution_iv` asserts the property rather
than trusting it.

Noise is handled by **pairing on task**, not by buying more runs: same task, same seed, same
model, only the configuration varies, and the analysis works on within-task differences. Task
difficulty is the dominant variance component on SWE-bench-style benchmarks, and blocking on it
is what turns an intractable sample size into a tractable one.

## Controls

An attribution without these is a number of unknown provenance.

- **Length-matched placebo.** Loading a skill lengthens the prompt. `psa.controls.make_placebo`
  writes an inert skill matched to the catalog's median length. Its `φ` must have a confidence
  interval containing zero — if it does not, the run set reports nothing.
- **Saboteur.** A deliberately harmful skill that must come out significantly negative. An
  instrument that cannot detect sabotage cannot be trusted to detect improvement.
- **Availability versus invocation.** Skills load by descriptor; the agent decides whether to
  use them. The ledger records both, and the report gives intention-to-treat *and*
  effect-among-invoked. A well-written skill that never triggers is worth nothing in practice.
- **Contamination.** Attribution ordering is re-checked on post-cutoff tasks. If it does not
  transfer, the finding was memorization, and that is what gets reported.

## Install

```bash
git clone https://github.com/rasputin28/principal-skill-analysis && cd principal-skill-analysis
python3 -m venv .venv && ./.venv/bin/pip install -e ".[dev]"
./.venv/bin/python -m pytest -q
```

## Use

```bash
# 1. pin a catalog — any repo of SKILL.md files, yours or someone else's
psa catalog ~/some-published-skills --out results/catalog.json

# 2. emit the run matrix
psa design results/catalog.json --stage screening --out results/design.json

# 3. execute (your harness, behind psa.runner.Runner) and append to the ledger

# 4. compute attributions from the ledger alone
psa estimate results/ledger.jsonl --out results/report.md
```

Step 4 never touches a model or a network. That boundary is deliberate: anyone can recompute
every number in the paper from the published ledger, without re-running a single agent, and
under a different estimator if they disagree with ours.

## Supporting a harness

`psa.runner.Runner` is a four-method protocol: prepare, run, return outcome, report which skills
were invoked. Implement it and your harness is measurable. A harness that cannot report
invocation is declared unsupported rather than approximated — without it, availability and
effect are indistinguishable.

`StubRunner` produces deterministic hashes so the pipeline can be exercised end to end before
any budget is spent. `psa.report.guard` refuses to turn a stub ledger into a result.

## Layout

```
psa/design.py      Hadamard construction, screening designs, full factorial
psa/estimate.py    exact + sampling Shapley, paired bootstrap, latent axes
psa/catalog.py     skill discovery and commit pinning
psa/compile.py     hermetic per-configuration workspaces
psa/ledger.py      the run record; the execution/analysis boundary
psa/controls.py    placebo and saboteur
psa/report.py      report cards that state failed controls rather than omitting them
paper.md           Stage 1 Registered Report
docs/superpowers/specs/  design document
```

## Citing

Suro, J. *Principal Skill Analysis: Attributing Agent Performance to Individual Skills and Their
Combinations.* Registered Report, Stage 1, 2026.

## License

MIT for the code. The paper is CC BY 4.0.
