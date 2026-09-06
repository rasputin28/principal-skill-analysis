"""Experimental designs.

Everything here is deterministic given its arguments and touches no model.
Hadamard matrices are *constructed*, never read from a table, so that their
defining property can be asserted in a test rather than trusted.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np


# --------------------------------------------------------------------------
# Hadamard construction
# --------------------------------------------------------------------------

def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def _legendre_symbol(a: int, p: int) -> int:
    """chi(a) over GF(p): 0 if a==0, +1 if a is a quadratic residue, else -1."""
    a %= p
    if a == 0:
        return 0
    return 1 if pow(a, (p - 1) // 2, p) == 1 else -1


def _paley_type_1(p: int) -> np.ndarray:
    """Hadamard matrix of order p+1 for prime p with p == 3 (mod 4).

    H = I + S, where S carries the Jacobsthal matrix of quadratic residues.
    """
    if not (_is_prime(p) and p % 4 == 3):
        raise ValueError(f"Paley type I needs a prime p = 3 (mod 4); got {p}")
    n = p + 1
    jacobsthal = np.array(
        [[_legendre_symbol(i - j, p) for j in range(p)] for i in range(p)], dtype=int
    )
    s = np.zeros((n, n), dtype=int)
    s[0, 1:] = 1
    s[1:, 0] = -1
    s[1:, 1:] = jacobsthal
    return s + np.eye(n, dtype=int)


def _sylvester(k: int) -> np.ndarray:
    """Hadamard matrix of order 2**k."""
    h = np.ones((1, 1), dtype=int)
    for _ in range(k):
        h = np.block([[h, h], [h, -h]])
    return h


def hadamard(n: int) -> np.ndarray:
    """Hadamard matrix of order ``n``.

    Built by Sylvester doubling over a Paley type I core. Raises for orders
    this construction cannot reach, rather than returning something that only
    looks like a design.
    """
    if n == 1:
        return np.ones((1, 1), dtype=int)
    if n % 4 != 0 and n != 2:
        raise ValueError(f"no Hadamard matrix of order {n}")
    # Try pure Sylvester first.
    if n & (n - 1) == 0:
        return _sylvester(int(math.log2(n)))
    # Otherwise peel factors of two down to a Paley core.
    doublings = 0
    core = n
    while core % 2 == 0 and not (_is_prime(core - 1) and (core - 1) % 4 == 3):
        core //= 2
        doublings += 1
    if not (_is_prime(core - 1) and (core - 1) % 4 == 3):
        raise ValueError(
            f"order {n} is not reachable by Paley type I plus Sylvester doubling"
        )
    h = _paley_type_1(core - 1)
    for _ in range(doublings):
        h = np.block([[h, h], [h, -h]])
    return h


def _normalize(h: np.ndarray) -> np.ndarray:
    """Put a Hadamard matrix in normal form: first row and column all +1."""
    h = h * np.where(h[0:1, :] < 0, -1, 1)
    h = h * np.where(h[:, 0:1] < 0, -1, 1)
    return h


# --------------------------------------------------------------------------
# Screening and full designs
# --------------------------------------------------------------------------

def _next_reachable_order(n_factors: int) -> int:
    n = 4 * ((n_factors // 4) + 1)
    while True:
        try:
            hadamard(n)
            return n
        except ValueError:
            n += 4


def plackett_burman(n_factors: int) -> np.ndarray:
    """Resolution III screening design as a (runs, n_factors) matrix of +-1."""
    if n_factors < 2:
        raise ValueError("need at least two factors")
    order = _next_reachable_order(n_factors)
    h = _normalize(hadamard(order))
    return h[:, 1 : n_factors + 1]


def foldover(design: np.ndarray) -> np.ndarray:
    """Raise a Resolution III design to Resolution IV by appending its mirror."""
    return np.vstack([design, -design])


def screening_design(n_factors: int, resolution: int = 4) -> np.ndarray:
    """The screening stage of PSA.

    Resolution IV is the default and the spec's choice: Resolution III aliases
    main effects with two-factor interactions, which are exactly the
    combination effects this instrument exists to detect.
    """
    base = plackett_burman(n_factors)
    if resolution == 3:
        return base
    if resolution == 4:
        return foldover(base)
    raise ValueError("resolution must be 3 or 4")


def full_factorial(n_factors: int) -> np.ndarray:
    """All 2**n_factors configurations as a (runs, n_factors) matrix of +-1."""
    if n_factors > 16:
        raise ValueError(
            f"2**{n_factors} configurations is not a design, it is a budget "
            "overrun; screen first"
        )
    rows = list(itertools.product([-1, 1], repeat=n_factors))
    return np.array(rows, dtype=int)


def permutation_samples(n_factors: int, n_permutations: int, seed: int) -> np.ndarray:
    """Random orderings of the factors, for the sampling Shapley estimator."""
    rng = np.random.default_rng(seed)
    return np.array(
        [rng.permutation(n_factors) for _ in range(n_permutations)], dtype=int
    )


# --------------------------------------------------------------------------
# Presentation
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Configuration:
    """One cell of the design: which skills are available to the agent."""

    index: int
    skills: tuple[str, ...]

    @property
    def key(self) -> frozenset[str]:
        return frozenset(self.skills)


def configurations(design: np.ndarray, skill_ids: list[str]) -> list[Configuration]:
    """Turn a +-1 design matrix into named skill subsets."""
    if design.shape[1] != len(skill_ids):
        raise ValueError(
            f"design has {design.shape[1]} factors but {len(skill_ids)} skills given"
        )
    out = []
    for i, row in enumerate(design):
        present = tuple(s for s, v in zip(skill_ids, row) if v > 0)
        out.append(Configuration(index=i, skills=present))
    return out


def main_effects(design: np.ndarray, response: np.ndarray) -> np.ndarray:
    """Main effect of each factor: mean(response | +1) - mean(response | -1)."""
    design = np.asarray(design)
    response = np.asarray(response, dtype=float)
    if design.shape[0] != response.shape[0]:
        raise ValueError("design and response disagree on the number of runs")
    effects = np.empty(design.shape[1])
    for j in range(design.shape[1]):
        hi = response[design[:, j] > 0]
        lo = response[design[:, j] < 0]
        effects[j] = hi.mean() - lo.mean()
    return effects
