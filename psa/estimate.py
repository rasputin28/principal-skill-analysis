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
