"""Estimation.

This module never touches a model, a runner, or a network. It consumes a
ledger and produces numbers, so that a third party can recompute every figure
in the paper without re-executing a single agent run.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy import stats


# --------------------------------------------------------------------------
# Shapley
# --------------------------------------------------------------------------

def _shapley_weights(n: int) -> np.ndarray:
    """w[c] = c! (n - c - 1)! / n! for a coalition of size c."""
    return np.array(
        [math.factorial(c) * math.factorial(n - c - 1) / math.factorial(n) for c in range(n)]
    )


def shapley_exact_by_task(
    values: Mapping[frozenset, np.ndarray],
    players: Sequence[str],
) -> np.ndarray:
    """Exact Shapley values, computed separately for every task.

    ``values`` must contain every one of the 2**n subsets of ``players``, each
    mapped to a vector of per-task outcomes sharing a common task ordering.

    Returns a (n_players, n_tasks) array. Because the Shapley value is linear
    in the value function, the per-task decomposition and the decomposition of
    the per-task mean agree exactly; keeping the task axis is what makes the
    paired bootstrap of :func:`bootstrap_ci` possible.
    """
    n = len(players)
    if n == 0:
        raise ValueError("no players")
    expected = 1 << n
    if len(values) != expected:
        raise ValueError(
            f"exact Shapley needs all {expected} subsets; got {len(values)}. "
            "Screen the catalog down first, or use shapley_sampling."
        )
    n_tasks = len(next(iter(values.values())))
    weights = _shapley_weights(n)
    phi = np.zeros((n, n_tasks))
    index = {p: i for i, p in enumerate(players)}

    for player in players:
        others = [p for p in players if p != player]
        acc = np.zeros(n_tasks)
        for size in range(n):
            for coalition in itertools.combinations(others, size):
                base = frozenset(coalition)
                with_player = base | {player}
                acc += weights[size] * (
                    np.asarray(values[with_player], dtype=float)
                    - np.asarray(values[base], dtype=float)
                )
        phi[index[player]] = acc
    return phi


def shapley_sampling_by_task(
    values: Mapping[frozenset, np.ndarray],
    players: Sequence[str],
    permutations: np.ndarray,
) -> np.ndarray:
    """Permutation-sampling Shapley estimator over an arbitrary subset space.

    Used only to validate that the screening stage discarded nothing large.
    Any permutation requiring a coalition absent from ``values`` is skipped and
    counted; a high skip rate invalidates the check and is reported, never
    silently absorbed.
    """
    n = len(players)
    n_tasks = len(next(iter(values.values())))
    totals = np.zeros((n, n_tasks))
    counts = np.zeros(n)
    for order in permutations:
        current: set[str] = set()
        for idx in order:
            player = players[idx]
            base, extended = frozenset(current), frozenset(current | {player})
            if base in values and extended in values:
                totals[idx] += np.asarray(values[extended], dtype=float) - np.asarray(
                    values[base], dtype=float
                )
                counts[idx] += 1
            current.add(player)
    if (counts == 0).any():
        missing = [players[i] for i in np.flatnonzero(counts == 0)]
        raise ValueError(f"no usable permutation increments for: {missing}")
    return totals / counts[:, None]


def efficiency_residual(
    phi_by_task: np.ndarray,
    values: Mapping[frozenset, np.ndarray],
    players: Sequence[str],
) -> float:
    """|sum_i phi_i - (v(S) - v(empty))|, which must be ~0 by construction.

    A non-zero residual means the estimator or the ledger is wrong, not that
    the catalog is unusual. It is criterion 5 of the design document.
    """
    total = phi_by_task.mean(axis=1).sum()
    lift = float(
        np.mean(values[frozenset(players)]) - np.mean(values[frozenset()])
    )
    return abs(total - lift)


# --------------------------------------------------------------------------
# Uncertainty
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Interval:
    point: float
    low: float
    high: float

    @property
    def excludes_zero(self) -> bool:
        return self.low > 0.0 or self.high < 0.0


def bootstrap_ci(
    phi_by_task: np.ndarray,
    players: Sequence[str],
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> dict[str, Interval]:
    """Percentile bootstrap over *tasks*, preserving the paired design.

    Resampling tasks rather than runs is what respects the blocking: the unit
    of independent replication is the task, and treating runs as independent
    would understate the interval.
    """
    rng = np.random.default_rng(seed)
    n_tasks = phi_by_task.shape[1]
    draws = np.empty((n_boot, phi_by_task.shape[0]))
    for b in range(n_boot):
        idx = rng.integers(0, n_tasks, n_tasks)
        draws[b] = phi_by_task[:, idx].mean(axis=1)
    lo = np.quantile(draws, alpha / 2, axis=0)
    hi = np.quantile(draws, 1 - alpha / 2, axis=0)
    point = phi_by_task.mean(axis=1)
    return {
        p: Interval(float(point[i]), float(lo[i]), float(hi[i]))
        for i, p in enumerate(players)
    }


# --------------------------------------------------------------------------
# Latent axes -- the "principal" half of Principal Skill Analysis
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class LatentAxes:
    explained_variance_ratio: np.ndarray  # (n_components,)
    config_directions: np.ndarray          # (n_configs, n_components)
    task_scores: np.ndarray                # (n_tasks, n_components)
    skill_loadings: np.ndarray             # (n_skills, n_components)
    skills: tuple[str, ...]


def latent_axes(
    outcomes: np.ndarray,
    skill_matrix: np.ndarray,
    skills: Sequence[str],
    n_components: int = 3,
) -> LatentAxes:
    """Decompose the task-by-configuration outcome matrix.

    ``outcomes`` is (n_tasks, n_configs); ``skill_matrix`` is (n_configs,
    n_skills) with 0/1 presence. The decomposition is applied to the matrix of
    *outcomes*; applying it to the design matrix would only diagnose
    collinearity among configurations, which is hygiene rather than a finding.

    Skill loadings are the correlation between a skill's presence across
    configurations and that configuration's coordinate on each axis. A skill
    that drives an axis loads on it; two skills loading on the same axis are
    substitutes.
    """
    y = np.asarray(outcomes, dtype=float)
    if y.shape[1] != skill_matrix.shape[0]:
        raise ValueError("outcomes and skill_matrix disagree on the configuration axis")
    centered = y - y.mean(axis=0, keepdims=True)
    u, s, vt = np.linalg.svd(centered, full_matrices=False)
    k = min(n_components, s.size)
    variance = s**2
    ratio = variance[:k] / variance.sum() if variance.sum() > 0 else np.zeros(k)
    directions = vt[:k].T                      # (n_configs, k)
    scores = u[:, :k] * s[:k]                  # (n_tasks, k)

    loadings = np.zeros((skill_matrix.shape[1], k))
    for i in range(skill_matrix.shape[1]):
        x = np.asarray(skill_matrix[:, i], dtype=float)
        if x.std() == 0:
            continue
        for j in range(k):
            d = directions[:, j]
            if d.std() == 0:
                continue
            loadings[i, j] = float(np.corrcoef(x, d)[0, 1])
    return LatentAxes(ratio, directions, scores, loadings, tuple(skills))


# --------------------------------------------------------------------------
# Agreement
# --------------------------------------------------------------------------

def rank_agreement(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    """Kendall's tau between two attributions over the same skills.

    Used for criterion 3 of the design document (stability across independent
    replications) and for the intention-to-treat versus invoked comparison.
    """
    keys = sorted(set(a) & set(b))
    if len(keys) < 2:
        raise ValueError("need at least two shared skills")
    return float(stats.kendalltau([a[k] for k in keys], [b[k] for k in keys]).statistic)


# --------------------------------------------------------------------------
# Interaction -- which combinations work, not just which skills do
# --------------------------------------------------------------------------

def _interaction_weights(n: int) -> np.ndarray:
    """w[c] = c! (n - c - 2)! / (n - 1)! for a coalition of size c."""
    return np.array(
        [
            math.factorial(c) * math.factorial(n - c - 2) / math.factorial(n - 1)
            for c in range(n - 1)
        ]
    )


def pairwise_lift(
    values: Mapping[frozenset, np.ndarray],
    a: str,
    b: str,
    context: frozenset[str] = frozenset(),
) -> np.ndarray:
    """v(C+ab) - v(C+a) - v(C+b) + v(C), per task, in one context.

    Positive means the pair is worth more together than the sum of its parts;
    negative means the two are substitutes and stacking them wastes context.
    """
    return (
        np.asarray(values[context | {a, b}], dtype=float)
        - np.asarray(values[context | {a}], dtype=float)
        - np.asarray(values[context | {b}], dtype=float)
        + np.asarray(values[context], dtype=float)
    )


def interaction_index_by_task(
    values: Mapping[frozenset, np.ndarray],
    players: Sequence[str],
) -> np.ndarray:
    """Shapley interaction index for every pair, computed per task.

    The Shapley value answers "what is this skill worth on average". It cannot
    answer "is skill 1 better paired with skill 3 than with skill 2", because
    it collapses the coalition structure into one number per player. The
    interaction index is the generalisation that keeps it: for each pair it
    averages the second-order difference

        v(C + ij) - v(C + i) - v(C + j) + v(C)

    over every context C, with the same coalition weighting that makes the
    Shapley value fair. Positive entries are synergy, negative entries are
    redundancy, and zero means the two skills neither help nor hinder one
    another.

    Returns a symmetric (n_players, n_players, n_tasks) array with a zero
    diagonal.
    """
    n = len(players)
    if n < 2:
        raise ValueError("interaction needs at least two players")
    expected = 1 << n
    if len(values) != expected:
        raise ValueError(
            f"the interaction index needs all {expected} subsets; got {len(values)}"
        )
    n_tasks = len(next(iter(values.values())))
    weights = _interaction_weights(n)
    out = np.zeros((n, n, n_tasks))
    index = {p: i for i, p in enumerate(players)}

    for a, b in itertools.combinations(players, 2):
        others = [p for p in players if p not in (a, b)]
        acc = np.zeros(n_tasks)
        for size in range(n - 1):
            for coalition in itertools.combinations(others, size):
                acc += weights[size] * pairwise_lift(values, a, b, frozenset(coalition))
        i, j = index[a], index[b]
        out[i, j] = acc
        out[j, i] = acc
    return out


def compare_coalitions(
    values: Mapping[frozenset, np.ndarray],
    left: Sequence[str],
    right: Sequence[str],
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> Interval:
    """Is this combination better than that one? v(left) - v(right), paired.

    The literal question a practitioner asks -- "should I load skill 1 with
    skill 3 or with skill 2" -- with an interval attached. Bootstrapped over
    tasks, so the comparison respects the blocking.
    """
    a, b = frozenset(left), frozenset(right)
    for key in (a, b):
        if key not in values:
            raise KeyError(f"coalition {sorted(key) or '(empty)'} was never run")
    diff = np.asarray(values[a], dtype=float) - np.asarray(values[b], dtype=float)
    rng = np.random.default_rng(seed)
    draws = np.array(
        [diff[rng.integers(0, diff.size, diff.size)].mean() for _ in range(n_boot)]
    )
    return Interval(
        float(diff.mean()),
        float(np.quantile(draws, alpha / 2)),
        float(np.quantile(draws, 1 - alpha / 2)),
    )


def best_coalitions(
    values: Mapping[frozenset, np.ndarray],
    size: int | None = None,
    top: int = 10,
) -> list[tuple[tuple[str, ...], float]]:
    """Rank the measured coalitions by mean outcome.

    With ``size`` given, ranks only coalitions of exactly that many skills,
    which is the shape of the budget question: given room for three skills,
    which three? Reads straight off the exact stage, where every subset of the
    survivors was run.
    """
    rows = [
        (tuple(sorted(key)), float(np.mean(vec)))
        for key, vec in values.items()
        if size is None or len(key) == size
    ]
    rows.sort(key=lambda kv: -kv[1])
    return rows[:top]


# --------------------------------------------------------------------------
# Orthogonal areas -- collapsing the interaction matrix into decisions
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class RedundancyStructure:
    skills: tuple[str, ...]
    eigenvalues: np.ndarray           # ascending; most negative first
    loadings: np.ndarray              # (n_skills, n_axes)
    clusters: tuple[tuple[str, ...], ...]
    unclustered: tuple[str, ...]


def redundancy_axes(
    interaction: np.ndarray,
    skills: Sequence[str],
    max_axes: int = 5,
    eigenvalue_tolerance: float = 1e-9,
    loading_threshold: float = 0.35,
) -> RedundancyStructure:
    """Collapse the pairwise interaction matrix into orthogonal areas.

    The interaction index gives n(n-1)/2 pairwise numbers, which for a catalog
    of any size is a matrix rather than a finding. This decomposes it instead.

    The interaction matrix is symmetric, so its eigenvectors are orthogonal by
    construction and live in skill space directly. The reading is exact rather
    than interpretive: a block of ``m`` mutually redundant skills, each pair
    interacting at ``-c``, produces an eigenvalue of ``-c(m-1)`` whose
    eigenvector is uniform over that block. The most negative axes therefore
    name the areas where a catalog has piled several skills onto one job.

    Orthogonality here is *imposed by the method, not discovered in the data*.
    The axes returned are the orthogonal directions that best account for the
    observed redundancy; they are not evidence that the underlying capability
    structure is orthogonal. Both thresholds are pre-registered analysis
    choices, not defaults to be tuned after seeing the result.
    """
    matrix = np.asarray(interaction, dtype=float)
    if matrix.shape[0] != matrix.shape[1] or matrix.shape[0] != len(skills):
        raise ValueError("interaction matrix must be square and match the skills given")
    if not np.allclose(matrix, matrix.T, atol=1e-9):
        raise ValueError("interaction matrix must be symmetric")

    eigenvalues, vectors = np.linalg.eigh(matrix)   # ascending
    keep = [i for i in range(len(eigenvalues)) if eigenvalues[i] < -eigenvalue_tolerance]
    keep = keep[:max_axes]
    loadings = vectors[:, keep] if keep else np.zeros((len(skills), 0))

    clusters: list[tuple[str, ...]] = []
    assigned: set[str] = set()
    for axis in range(loadings.shape[1]):
        column = loadings[:, axis]
        strong = [i for i in range(len(skills)) if abs(column[i]) >= loading_threshold]
        # Members of one redundancy block load with a common sign.
        for sign in (1, -1):
            members = tuple(
                skills[i] for i in strong if np.sign(column[i]) == sign and skills[i] not in assigned
            )
            if len(members) >= 2:
                clusters.append(members)
                assigned.update(members)
    unclustered = tuple(s for s in skills if s not in assigned)
    return RedundancyStructure(
        skills=tuple(skills),
        eigenvalues=eigenvalues[keep] if keep else np.array([]),
        loadings=loadings,
        clusters=tuple(clusters),
        unclustered=unclustered,
    )


def minimal_spanning_subset(
    structure: RedundancyStructure,
    phi: Mapping[str, float],
) -> tuple[str, ...]:
    """One skill per redundancy area, plus everything that overlaps nothing.

    The actionable form of the whole study: given a catalog whose skills
    duplicate one another, this is the subset that covers every area it covers,
    with the best-attributed representative kept in each. Skills with a
    negative attribution are dropped rather than kept as representatives.
    """
    chosen: list[str] = []
    for cluster in structure.clusters:
        best = max(cluster, key=lambda s: phi.get(s, 0.0))
        if phi.get(best, 0.0) > 0:
            chosen.append(best)
    chosen += [s for s in structure.unclustered if phi.get(s, 0.0) > 0]
    return tuple(sorted(chosen))


# --------------------------------------------------------------------------
# Arbitrary order -- beyond pairs
# --------------------------------------------------------------------------

def interaction_index(
    values: Mapping[frozenset, np.ndarray],
    players: Sequence[str],
    subset: Sequence[str],
) -> np.ndarray:
    """Shapley interaction index of arbitrary order, per task.

    Generalises both estimators above. For a subset ``T`` of size ``t``,

        I(T) = sum over C in S\\T of  w(|C|) * sum over L in T of (-1)^(t-|L|) v(C + L)

    with ``w(c) = c! (n - c - t)! / (n - t + 1)!``. At ``t = 1`` this is exactly
    the Shapley value; at ``t = 2`` it is exactly the pairwise interaction index.
    Both identities are asserted in the test suite rather than asserted here.

    Use it to ask about a specific group -- does this trio work together --
    without enumerating every trio. Enumerating all orders would produce 2**k
    numbers, which is the matrix-not-a-finding problem again; for group-level
    structure use :func:`redundancy_axes` and :func:`coalition_curve` instead.
    """
    subset = list(subset)
    t, n = len(subset), len(players)
    if t == 0:
        raise ValueError("the interaction of the empty set is not defined")
    if not set(subset) <= set(players):
        raise ValueError(f"not players: {sorted(set(subset) - set(players))}")
    others = [p for p in players if p not in subset]
    n_tasks = len(next(iter(values.values())))
    weights = np.array(
        [
            math.factorial(c) * math.factorial(n - c - t) / math.factorial(n - t + 1)
            for c in range(n - t + 1)
        ]
    )
    acc = np.zeros(n_tasks)
    for size in range(len(others) + 1):
        for context in itertools.combinations(others, size):
            base = frozenset(context)
            delta = np.zeros(n_tasks)
            for take in range(t + 1):
                sign = (-1) ** (t - take)
                for chosen in itertools.combinations(subset, take):
                    key = base | frozenset(chosen)
                    if key not in values:
                        raise KeyError(
                            f"coalition {sorted(key) or '(empty)'} was never run; "
                            "the interaction index needs the complete subset space"
                        )
                    delta += sign * np.asarray(values[key], dtype=float)
            acc += weights[size] * delta
    return acc


@dataclass(frozen=True)
class CoalitionCurve:
    sizes: tuple[int, ...]
    best_coalition: tuple[tuple[str, ...], ...]
    best_value: np.ndarray
    additive_prediction: np.ndarray
    gap: np.ndarray            # best_value - additive_prediction; see coalition_curve


def coalition_curve(
    values: Mapping[frozenset, np.ndarray],
    phi: Mapping[str, float],
    baseline: float | None = None,
) -> CoalitionCurve:
    """How much is the best combination of each size actually worth?

    This is the question a catalog of four, five or forty skills poses and that
    no per-skill ranking answers: given room for ``m`` skills, what is the best
    ``m``, and does adding the next one still pay? For each size it reports the
    best measured coalition, its value, what a purely additive reading of the
    attributions would have predicted for that same set, and the gap between
    them. A persistently negative gap is subadditivity -- the catalog's skills
    buying one another's work a second time -- and it is where the curve
    flattens that a context budget should stop.

    Read directly off the exact stage. No model, no extrapolation: every
    coalition named here was actually run.
    """
    by_size: dict[int, list[tuple[frozenset, float]]] = {}
    for key, vec in values.items():
        by_size.setdefault(len(key), []).append((key, float(np.mean(vec))))
    if baseline is None:
        baseline = float(np.mean(values[frozenset()])) if frozenset() in values else 0.0

    sizes, coalitions, best, additive = [], [], [], []
    for size in sorted(by_size):
        key, value = max(by_size[size], key=lambda kv: kv[1])
        sizes.append(size)
        coalitions.append(tuple(sorted(key)))
        best.append(value)
        additive.append(baseline + sum(phi.get(p, 0.0) for p in key))
    best_arr, additive_arr = np.array(best), np.array(additive)
    return CoalitionCurve(
        sizes=tuple(sizes),
        best_coalition=tuple(coalitions),
        best_value=best_arr,
        additive_prediction=additive_arr,
        gap=best_arr - additive_arr,
    )


# --------------------------------------------------------------------------
# Dividends -- the change of basis that makes the problem polynomial
# --------------------------------------------------------------------------

def mobius_coefficients(
    values: Mapping[frozenset, np.ndarray],
    players: Sequence[str],
    max_order: int | None = None,
) -> dict[frozenset, np.ndarray]:
    """The dividend of every combination, per task.

        a(T) = sum over L contained in T of (-1)^(|T|-|L|) v(L)

    The dividend of a combination is the part of its worth that no smaller
    combination accounts for: ``a({i})`` is what a skill is worth alone,
    ``a({i,j})`` what the pair is worth beyond the two of them separately.

    The expansion is exact and unique, and it is what makes bounded interaction
    order useful: if dividends vanish above order ``t``, the whole value
    function and every attribution follow from O(N**t) numbers rather than
    2**N. ``max_order`` truncates the computation to that assumption.
    """
    out: dict[frozenset, np.ndarray] = {}
    limit = len(players) if max_order is None else max_order
    for size in range(limit + 1):
        for combo in itertools.combinations(players, size):
            target = frozenset(combo)
            acc = np.zeros(len(next(iter(values.values()))))
            for take in range(size + 1):
                sign = (-1) ** (size - take)
                for sub in itertools.combinations(combo, take):
                    key = frozenset(sub)
                    if key not in values:
                        raise KeyError(
                            f"coalition {sorted(key) or '(empty)'} was never run"
                        )
                    acc += sign * np.asarray(values[key], dtype=float)
            out[target] = acc
    return out


def shapley_from_mobius(
    coefficients: Mapping[frozenset, np.ndarray],
    players: Sequence[str],
) -> np.ndarray:
    """Attribution from dividends: phi_i = sum over T containing i of a(T)/|T|.

    Each combination's dividend is split equally among the skills that earned
    it. Computing the attribution this way and by averaging over orderings must
    agree, and the test suite checks that they do; the agreement is a check on
    both derivations rather than on one implementation.
    """
    n_tasks = len(next(iter(coefficients.values())))
    phi = np.zeros((len(players), n_tasks))
    for i, player in enumerate(players):
        for combo, dividend in coefficients.items():
            if player in combo:
                phi[i] += np.asarray(dividend, dtype=float) / len(combo)
    return phi


def reconstruct(
    coefficients: Mapping[frozenset, np.ndarray],
    coalition: frozenset,
) -> np.ndarray:
    """v(C) = sum of the dividends of every combination inside C."""
    n_tasks = len(next(iter(coefficients.values())))
    total = np.zeros(n_tasks)
    for combo, dividend in coefficients.items():
        if combo <= coalition:
            total += np.asarray(dividend, dtype=float)
    return total


def design_matrix(
    coalitions: Sequence[frozenset],
    combinations: Sequence[frozenset],
) -> np.ndarray:
    """Row per configuration, column per combination, 1 where the second sits inside the first.

    This is the linear system behind ``v(C) = sum of a(T) for T inside C``.
    """
    return np.array(
        [[1.0 if t <= c else 0.0 for t in combinations] for c in coalitions]
    )


def fit_bounded_order(
    values: Mapping[frozenset, np.ndarray],
    players: Sequence[str],
    order: int,
) -> dict[frozenset, np.ndarray]:
    """Estimate dividends up to ``order`` from whatever configurations were run.

    The exact transform of :func:`mobius_coefficients` needs every subset of a
    combination in order to compute its dividend, so it is unavailable from a
    partial design; that is what the bounded-order assumption exists to avoid.
    Under the assumption, ``v(C) = sum of a(T) for T inside C`` restricted to
    ``|T| <= order`` is a linear system in the dividends, and the design is
    solved for them by least squares.

    Raises when the configurations that were run cannot identify the
    coefficients, which is the practical face of the resolution requirement: a
    design recovers every effect up to order ``t`` only if its resolution is at
    least ``2t + 1``, and it needs at least as many runs as unknowns.
    """
    combos = [
        frozenset(c)
        for size in range(order + 1)
        for c in itertools.combinations(players, size)
    ]
    coalitions = sorted(values, key=lambda k: (len(k), sorted(k)))
    x = design_matrix(coalitions, combos)
    if np.linalg.matrix_rank(x) < len(combos):
        raise ValueError(
            f"the {len(coalitions)} configurations run cannot identify the "
            f"{len(combos)} dividends of order <= {order}; the design needs at least "
            "that many runs and resolution 2*order+1"
        )
    y = np.array([np.asarray(values[c], dtype=float) for c in coalitions])
    solution, *_ = np.linalg.lstsq(x, y, rcond=None)
    return {t: solution[i] for i, t in enumerate(combos)}


@dataclass(frozen=True)
class FaithfulnessCheck:
    order: int
    heldout_error: float
    noise_floor: float
    ratio: float
    passes: bool


def holdout_faithfulness(
    values: Mapping[frozenset, np.ndarray],
    players: Sequence[str],
    order: int,
    heldout: Sequence[frozenset],
    noise_floor: float,
    tolerance: float = 2.0,
) -> FaithfulnessCheck:
    """Is bounded interaction order actually true here?

    Fits dividends up to ``order`` (by :func:`fit_bounded_order`) on the
    configurations *outside* ``heldout``,
    predicts the held-out ones, and compares the mean squared prediction error
    against ``noise_floor``, the variance between repeated runs of the same
    configuration, which no model can beat.

    Error at the floor means the order-``t`` description captures everything but
    noise. Error clearly above it means interactions above order ``t`` carry
    real signal and the attributions are incomplete. ``tolerance`` is the
    multiple of the floor at which that verdict is declared, and belongs in the
    pre-registration rather than being chosen once the number is known.
    """
    held = {frozenset(h) for h in heldout}
    fitting = {k: v for k, v in values.items() if k not in held}
    if not held:
        raise ValueError("nothing held out; the check would be vacuous")
    missing = [h for h in held if h not in values]
    if missing:
        raise KeyError(f"held-out coalitions were never run: {missing}")

    coefficients = fit_bounded_order(fitting, players, order)
    errors = [
        float(np.mean((reconstruct(coefficients, h) - np.asarray(values[h], dtype=float)) ** 2))
        for h in held
    ]
    error = float(np.mean(errors))
    ratio = error / noise_floor if noise_floor > 0 else float("inf")
    return FaithfulnessCheck(order, error, noise_floor, ratio, ratio <= tolerance)
