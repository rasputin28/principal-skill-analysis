# Principal Skill Analysis: Attributing Agent Performance to Individual Skills and Their Combinations

**Joel Suro**

*Registered Report, Stage 1 — pre-registration. No experimental results are reported in this
document. Sections 6 and 7 state hypotheses and the analysis plan that will be applied to data
not yet collected.*

---

## Abstract

The practice of extending coding agents with curated collections of natural-language
instructions—variously called skills, harnesses, or frameworks—has grown faster than the
methods available to evaluate them. Authors publish collections and report aggregate
improvements, but the field has no instrument for determining which components of a collection
earn that improvement, whether some components contribute nothing, or whether two collections
published by different authors can be compared at all. The question is empirical and is
currently answered rhetorically. In this work, I propose Principal Skill Analysis (PSA), a
measurement instrument that treats a skill collection as an input rather than as the object of
a single study. PSA estimates the marginal contribution of each skill through its Shapley
value over the space of skill subsets, which guarantees that individual contributions sum
exactly to the aggregate improvement of the full collection, and it recovers latent axes of
task demand by decomposing the task-by-configuration outcome matrix, which reveals which
skills are redundant with one another and which subset spans the space. Because the subset
space grows as `2^N`, I combine a Resolution IV fractional factorial screening stage with an
exact Shapley computation over the surviving factors, and I address the dominant source of
noise—task difficulty—through a task-paired design rather than through additional sampling. I
further specify the negative and positive controls without which such measurements are not
attributable: a length-matched placebo skill whose estimated contribution must be
indistinguishable from zero, and an instrumented record of whether each skill was actually
invoked rather than merely made available. I hypothesize that a small minority of skills
accounts for the majority of the measurable gain, that the gap between a skill being available
and a skill being invoked is large enough to dominate the ranking, and consequently that the
choice of which skills to load has a far greater effect on reported agent performance than the
size or provenance of the collection they are drawn from.

---

## 1. Introduction

Coding agents built on large language models are now routinely extended with collections of
written instructions that the model can load on demand. These collections go by different names
across ecosystems, and their authors describe them in the vocabulary of software engineering
practice: test-first development, systematic debugging, verification before completion,
planning before implementation. A collection is published, adopted, and defended, and the
defense takes the form of an assertion that the collection improves outcomes.

The assertion is rarely accompanied by a measurement, and when it is, the measurement is
aggregate. A collection is evaluated whole. This leaves three questions unanswered, and they
are the questions a practitioner actually has.

The first is attribution. If a collection of twenty skills improves a benchmark by some margin,
which of the twenty produced the margin? Aggregate evaluation cannot say. It is entirely
consistent with the observed data that two skills produced the entire effect and eighteen
produced none, and it is equally consistent that all twenty contributed evenly. These two
worlds imply opposite recommendations to a practitioner deciding what to load into a limited
context window, and current practice cannot distinguish them.

The second is combination. The standard remedy for attribution is the ablation: remove one
component, observe the change. This procedure conflates two different things. A skill that
contributes nothing and a skill that contributes only in the presence of another skill both
appear as null under leave-one-out ablation, because removing either one from the full
collection leaves the rest of the collection to compensate. The distinction matters, because
the second kind of skill is not removable and the first kind is.

The third is comparability. Two collections published by two authors cannot be compared against
each other because they were never measured against the same baseline, the same model, or the
same seeds. Each author reports a number computed under their own conditions, and the numbers
do not meet.

I address all three by treating the skill collection as an input to a measurement instrument
rather than as the subject of a bespoke study. The instrument accepts a collection identified
by repository and commit, evaluates it against a fixed baseline agent on a fixed benchmark, and
returns a per-skill attribution with confidence intervals, a decomposition into latent axes of
task demand, and—when given more than one collection—a comparison on a common footing.

The central estimand is the Shapley value of each skill over the space of skill subsets. I
choose it not for its familiarity in interpretable machine learning but for a property that is
load-bearing here: efficiency. The individual attributions sum exactly to the improvement of the
full collection over the bare agent. A ranked plot of those attributions is therefore a genuine
decomposition of the total, not a normalized ranking that merely resembles one. This is the
sense in which the method is analogous to principal component analysis, and it is also the sense
in which the analogy must be stated carefully, as I do in Section 4.

I name the second estimand more directly after that analogy. Decomposing the matrix of outcomes
across tasks and configurations recovers axes along which tasks succeed and fail together.
Projecting skills onto those axes converts the result from a list of numbers into a position in
a space, which is what permits statements about redundancy and coverage: that two skills load on
the same axis and are therefore substitutes, or that a collection covers verification but leaves
exploration unaddressed.

This document is a pre-registration. The design, the hypotheses, and the analysis plan are fixed
here, before data collection, because the space of configurations is large enough that a
determined analyst can always find a configuration producing an attractive result. A study of
this shape that is not pre-registered is not defensible, and I would not believe one.

## 2. Related Work

**Benchmarks for coding agents.** SWE-bench [Jimenez et al., 2024] established the practice of
evaluating agents on real repository issues with automated verification through the repository's
own test suite, and SWE-bench Verified [OpenAI, 2024] produced a human-validated subset in
which the tests are known to discriminate correct from incorrect patches. The binary
pass-or-fail outcome that these benchmarks provide is what makes the present work feasible:
without an automatic and trustworthy verdict, the number of runs this design requires would be
impossible to grade. Agent harnesses evaluated on these benchmarks, such as SWE-agent [Yang et
al., 2024], are typically reported as complete systems, which is precisely the aggregate
reporting this work seeks to decompose.

**Attribution by Shapley value.** The Shapley value [Shapley, 1953] was introduced to distribute
the payoff of a cooperative game among its players, and it is the unique allocation satisfying
efficiency, symmetry, the null-player property, and linearity. Its adoption in machine learning
has been broad: SHAP [Lundberg and Lee, 2017] applies it to feature attribution in model
predictions, and Data Shapley [Ghorbani and Zou, 2019] applies it to valuing individual training
examples. In both cases the computational obstacle is the same one that appears here—the number
of coalitions grows exponentially—and in both cases the standard remedy is sampling. I take a
different route, described in Section 5, because the effect sizes I expect are small enough that
a sampling estimator's variance would dominate the quantity being estimated.

**Design of experiments.** The screening problem—identifying which of many factors matter, using
far fewer runs than the full factorial—is old and well solved. Plackett–Burman designs
[Plackett and Burman, 1946] estimate `N` main effects in a number of runs proportional to `N`
rather than exponential in it, and the foldover construction that raises such a design from
Resolution III to Resolution IV is standard [Box, Hunter and Hunter, 2005]. The relevance of the
resolution distinction to this particular problem is direct and is argued in Section 5.1.

**Pre-registration.** The Registered Report format [Chambers, 2013] was introduced in response to
the same structural problem that this study faces: a large analytic degrees of freedom combined
with an incentive to report positive findings. I follow its Stage 1 structure.

**Prior work by the author.** The concern that motivates this study—that probabilistic systems
are routinely reported as more reliable than their verification supports—also motivated my
earlier work on introducing deterministic evaluation into retrieval-augmented generation [Suro,
2024]. The present work applies the same instinct one level up, to the evaluation of the agent
scaffolding itself.

## 3. Problem Formulation

Let `S = {s₁, …, s_N}` denote the catalog of skills under test, and let a configuration `C ⊆ S`
be the subset of skills made available to the agent during a run. Let `T` denote the set of
benchmark tasks and let `Y(t, C, r)` denote the outcome of run `r` on task `t` under
configuration `C`. Define the value function

```
v(C) = E_{t ∈ T, r} [ Y(t, C, r) ]
```

so that `v(∅)` is the performance of the bare agent and `v(S)` the performance of the agent with
the entire catalog available. The quantity to be distributed among the skills is the total lift
`v(S) − v(∅)`.

## 4. Estimands

### 4.1 Per-skill attribution

The Shapley value of skill `i` is

```
φᵢ = Σ_{C ⊆ S \ {i}}  [ |C|! (N − |C| − 1)! / N! ] · [ v(C ∪ {i}) − v(C) ]
```

Four of its properties are load-bearing in this application. Efficiency gives `Σᵢ φᵢ = v(S) −
v(∅)`, so the attributions constitute a decomposition of the total lift rather than a ranking
normalized to resemble one. The null-player property assigns exactly zero to a skill that never
changes an outcome, which is the statement a practitioner needs in order to justify not loading
it. Symmetry assigns equal value to interchangeable skills. And the averaging over all
coalitions `C` is what recovers combination effects: a skill that contributes only alongside
another contributes positively in the coalitions containing that other skill, and this survives
the average, whereas it vanishes entirely under leave-one-out ablation.

### 4.2 Latent axes of task demand

Let `Y` be the matrix whose rows are tasks and whose columns are the evaluated configurations,
with entries given by the observed outcomes. Principal component analysis of `Y` yields
components that group tasks succeeding and failing together—latent axes of what a task demands
of an agent. Skills are then projected onto these axes.

Two clarifications are necessary, because the analogy that gives this work its name is also the
easiest thing about it to misread. First, the decomposition is applied to the matrix of
*outcomes*, not to the matrix of *design*. Applying it to the design matrix would diagnose
collinearity among configurations, which is a hygiene check rather than a finding. Second,
principal component analysis is unsupervised and therefore cannot on its own establish that a
skill causes an improvement; it organizes the structure of a set of measurements whose causal
interpretation is supplied by the randomized design of Section 5, not by the decomposition.

### 4.3 Interaction structure: which combinations work

The Shapley value answers what a skill is worth on average. It does not answer the question a
practitioner actually faces when context is scarce, which is whether skill 1 is better paired
with skill 3 than with skill 2. That question survives the averaging only if the coalition
structure is kept rather than collapsed, and the object that keeps it is the Shapley interaction
index. For a pair `{i, j}` it averages the second-order difference

```
Delta_ij(C) = v(C + i + j) - v(C + i) - v(C + j) + v(C)
```

over every context `C`, weighted so that the same fairness axioms that justify the per-skill
allocation carry over to the pair. A positive index is synergy: the two skills are worth more
together than the sum of their separate contributions. A negative index is redundancy: they do
the same job, and loading both spends context to buy what one already bought. Zero means they
neither help nor hinder each other.

I record this as a first-class result rather than a diagnostic, because it is the quantity that
distinguishes a catalog from a list. A catalog whose skills are mutually redundant has a total
lift far below the sum of its parts and can be replaced by a small subset with no loss; a
catalog whose skills are complementary cannot. Aggregate evaluation cannot tell these apart, and
neither can a per-skill ranking.

The exact stage of Section 5.2 enumerates every subset of the surviving skills, so every pairwise
index — and every higher-order one — is computed exactly from the same runs, with no additional
budget. The screening stage does not identify pairs: a Resolution IV design separates main
effects from two-factor interactions but leaves two-factor interactions aliased with one another,
and separating those would require Resolution V at substantially greater cost. What Resolution IV
does guarantee is that a skill carrying a strong interaction is not discarded before the exact
stage can measure it, because in a balanced design a skill whose entire value is a pairwise
interaction still shifts the marginal mean: its partner is present in half of the runs.

### 4.4 Comparison across catalogs

For two catalogs `A` and `B` evaluated with the same base agent, benchmark, model and seeds, the
comparable quantities are the total lifts `v(S_A) − v(∅)` and `v(S_B) − v(∅)`, the same lifts
normalized by cost in tokens and turns, and the overlap of the two catalogs in the latent space
of Section 4.2.

Individual `φ` values are not comparable across catalogs, because each is an allocation internal
to its own coalition structure: the same skill placed in a catalog of redundant peers receives a
smaller share than it would in a catalog of complements, and this is correct behavior rather
than an artifact. The total is comparable; the shares are not. I state this prominently because
it is the most likely misuse of the instrument.

## 5. Design

The full factorial is unavailable: at `N = 20`, the subset space contains more than a million
configurations. The design proceeds in two stages with a validation pass.

### 5.1 Screening

The first stage uses a Resolution IV fractional factorial design, constructed as a
Plackett–Burman design followed by its foldover, requiring `2 · ceil₄(N + 1)` configurations—48
for any catalog of 23 skills or fewer. Skills whose main effects are not distinguishable from
zero are set aside; the number retained is fixed in advance rather than chosen after inspecting
the estimates.

The choice of Resolution IV over the cheaper Resolution III is the single most consequential
decision in the design, and it follows directly from the question. A Resolution III design
aliases main effects with two-factor interactions. A skill that contributes only in combination
with one other skill is exactly a two-factor interaction, and under Resolution III its
contribution is confounded with a main effect and may be discarded at this stage. Since
combination effects are the phenomenon this work exists to detect, halving the screening budget
by aliasing them away would defeat the study. Resolution IV aliases main effects with
three-factor interactions instead, a risk I accept and record. It also preserves, rather than
identifies, the two-factor interactions themselves; identification happens in the exact stage,
where every subset of the survivors is run and every interaction of every order is therefore
available without additional cost.

### 5.2 Exact computation

The second stage runs the complete factorial over the `k` surviving skills—128 configurations at
`k = 7`—and computes Shapley values exactly. No sampling estimator, no surrogate model, no
approximation whose bias a reviewer would have to take on faith. Interactions of every order are
captured by construction.

### 5.3 Validation of the screen

A permutation-sampling Shapley estimator is run over the *complete* catalog at reduced budget,
solely to check that no skill discarded in screening carries a large attribution. Should one
appear, it is reported as a failure of the screening design rather than silently corrected. The
purpose of this pass is to make the two-stage shortcut falsifiable.

## 6. Power

The outcome is Bernoulli and the agent is stochastic. Detecting a lift of a few percentage
points under independent sampling would require thousands of runs per comparison, which is not
affordable. Three levers make the design feasible, and they are listed in descending order of
effect.

The first and largest is **pairing on task**. Each comparison holds the task, the seed, and the
model fixed and varies only the configuration, and the analysis operates on within-task
differences. This removes the variance due to task difficulty, which on SWE-bench dominates
every other source: some tasks are solved by nearly every configuration and some by none, and
the between-group variance induced by this heterogeneity is far larger than the effect being
estimated. Blocking on task converts an intractable sample size requirement into a tractable
one.

The second is a **richer outcome than the binary verdict**. Recording only whether a task was
resolved discards information available in the same run. I additionally record the fraction of
fail-to-pass tests satisfied, the number of turns to solution, the tokens consumed, and whether
the patch touched the files the reference patch touched. The primary outcome is declared in the
pre-registration; the remainder are secondary. The cost measures are not merely covariates: a
skill that buys two points of accuracy at triple the token cost is a different product from one
that buys the same two points for free, and reporting the lift without the cost would be
incomplete.

The third is **restriction to the informative band**. A pilot classifies tasks by their
difficulty under the baseline. Tasks the baseline always solves and tasks it never solves carry
no information about skills, and including them purchases runs without purchasing signal.
Restricting to the intermediate band raises signal per run. The cutoff is fixed in advance and
the excluded tasks are published.

Confidence intervals are obtained by bootstrapping over tasks rather than over runs, preserving
the pairing.

## 7. Controls

Four controls are required. Without them the measurements are not attributable to skills, and I
would not accept them from another author.

**A length-matched placebo.** Loading a skill lengthens the prompt. A skill could appear to work
for no reason other than that it added context. Every design therefore includes a placebo skill
whose token length matches the catalog median and whose content is plausible in form but carries
no actionable instruction. Its estimated attribution must have a confidence interval containing
zero. If it does not, the instrument is miscalibrated and no results are reported from that run
set. This is the negative control that validates the entire apparatus, and it is checked before
any quantity of interest is examined.

**Availability versus invocation.** Skills are loaded by descriptor and the agent decides whether
to invoke them. An uninvoked skill contributes nothing, and an experiment that does not
distinguish the two is measuring availability while claiming to measure effect. Traces are
instrumented to record actual invocation, and both quantities are reported: the
intention-to-treat estimate over assigned configurations, and the effect among runs in which the
skill was invoked. The gap between them is itself a finding. A well-written skill that never
triggers is worth nothing in practice, and I expect this gap to be large.

**Benchmark contamination.** SWE-bench Verified predates the training cutoff of current models,
so an attribution may reflect memorization rather than capability. I therefore evaluate the
ordering of attributions on a post-cutoff validation set drawn from repositories outside the
benchmark. If the ordering transfers, the finding concerns skills; if it does not, the finding
concerned memorization, and that is reported as such.

**Declared scope.** Attributions may reorder across base models and across harnesses. Either at
least two models and two harnesses are run, or the scope is stated in the finding itself rather
than left implicit.

## 8. Hypotheses

These are fixed before data collection.

**H1 (concentration).** The distribution of `|φᵢ|` is heavily concentrated: fewer than one third
of the skills in a typical published catalog account for more than two thirds of the total lift.

**H2 (null mass).** A substantial fraction of skills in a typical published catalog have
attributions whose confidence intervals contain zero.

**H3 (combination).** At least one skill exhibits a positive attribution under the coalition
average while showing no distinguishable effect under leave-one-out ablation—that is, at least
one skill is detectable only in combination.

**H4 (invocation gap).** The rank correlation between intention-to-treat attributions and
effect-among-invoked attributions is substantially below unity, and at least one skill ranked
highly on invocation ranks low on assignment because it is rarely triggered.

**H6 (subadditivity).** Pairwise interaction indices within a published catalog are
predominantly negative rather than positive: skills in these collections substitute for one
another more often than they complement one another, so a catalog's total lift falls short of
the sum of its parts and a small subset reproduces most of it.

**H5 (composition over provenance).** Between two catalogs matched on total token budget, the
difference in total lift attributable to *which* skills are included exceeds the difference
attributable to catalog size or authorship.

H2, H5 and H6 are the hypotheses whose confirmation would most change practice, and all three are
uncomfortable for the field this work is addressed to. H6 in particular contradicts the implicit
assumption under which these collections are assembled and adopted, which is that adding a skill
is weakly beneficial. I state them in that form deliberately. A null result on H1 through H6—no skill distinguishable from zero at achievable
budget—is a publishable outcome and will be reported without reframing.

## 9. Reproducibility

The analysis stage is separated from the execution stage by a published run ledger. Every run
contributes a record containing the catalog commit, the configuration, the task, the seed, the
model version, the outcomes, and the invocation trace. All reported quantities are computed from
this ledger alone, so that a third party can reproduce every number in the results without
re-executing a single agent run, and can recompute them under a different estimator if they
disagree with mine.

The pre-registration is committed and hashed before the first measurement run, and the hash is
cited in the final report.

## 10. Limitations

The instrument measures a catalog under a fixed base agent, benchmark, model and harness, and
attributions are conditional on all four. It does not establish that a skill is well written,
only that its presence changed outcomes under these conditions. It cannot distinguish a skill
that improves the agent's reasoning from one that merely constrains its output format into
better alignment with the grader. The two-stage design trades exhaustiveness for feasibility and
its screening stage can discard a skill whose contribution requires three or more partners; the
validation pass of Section 5.3 bounds but does not eliminate this risk. Finally, the cost of the
design scales with the product of configurations, tasks and repetitions, and the budget is the
binding constraint on how many catalogs can be measured.

## 11. Conclusion

The disagreement over which agent scaffolding works is an empirical question that the field
currently settles by assertion. I have specified an instrument that settles it by measurement:
Shapley attribution over skill subsets for the per-skill question, a decomposition of the
outcome matrix for the redundancy and coverage question, a two-stage design that makes both
computable, a task-paired analysis that makes both affordable, and a set of controls—chief among
them a length-matched placebo and an invocation trace—that make both attributable. The
instrument takes the catalog as an input, so that a collection published by any author can be
measured on the same footing as any other, which is the condition under which the disagreement
can be resolved rather than repeated.

---

## References

*Every reference below must be verified against its source before submission.*

- Box, G. E. P., Hunter, J. S., and Hunter, W. G. (2005). *Statistics for Experimenters: Design,
  Innovation, and Discovery*, 2nd edition. Wiley.
- Chambers, C. D. (2013). Registered Reports: A new publishing initiative at Cortex. *Cortex*,
  49(3), 609–610.
- Ghorbani, A. and Zou, J. (2019). Data Shapley: Equitable Valuation of Data for Machine
  Learning. *ICML*.
- Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., and Narasimhan, K. (2024).
  SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR*.
- Lundberg, S. M. and Lee, S.-I. (2017). A Unified Approach to Interpreting Model Predictions.
  *NeurIPS*.
- OpenAI (2024). Introducing SWE-bench Verified.
- Plackett, R. L. and Burman, J. P. (1946). The Design of Optimum Multifactorial Experiments.
  *Biometrika*, 33(4), 305–325.
- Shapley, L. S. (1953). A Value for n-Person Games. In *Contributions to the Theory of Games,
  Volume II*. Princeton University Press.
- Suro, J. (2024). Semantic Tokens in Retrieval Augmented Generation. arXiv:2412.02563.
- Yang, J., Jimenez, C. E., Wettig, A., Lieret, K., Yao, S., Narasimhan, K., and Press, O.
  (2024). SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. *NeurIPS*.
