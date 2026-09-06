import itertools

import numpy as np
import pytest

from psa import design


REACHABLE = [4, 8, 12, 16, 20, 24, 32, 40, 44, 48]


@pytest.mark.parametrize("n", REACHABLE)
def test_hadamard_defining_property(n):
    h = design.hadamard(n)
    assert set(np.unique(h)) <= {-1, 1}
    assert np.array_equal(h @ h.T, n * np.eye(n, dtype=int))


def test_unreachable_order_raises_rather_than_lying():
    with pytest.raises(ValueError):
        design.hadamard(6)


def test_screening_size_matches_the_spec():
    # 20 skills must screen in 48 runs at Resolution IV.
    assert design.screening_design(20).shape == (48, 20)
    assert design.screening_design(20, resolution=3).shape == (24, 20)


def test_resolution_iii_main_effects_are_orthogonal():
    d = design.plackett_burman(11)
    gram = d.T @ d
    assert np.array_equal(np.diag(gram), np.full(11, d.shape[0]))
    off = gram - np.diag(np.diag(gram))
    assert np.count_nonzero(off) == 0


def test_foldover_actually_buys_resolution_iv():
    """Every two-factor interaction must be orthogonal to every main effect.

    This is the property the design document pays double the screening budget
    for, and the reason Resolution III is rejected: under Resolution III a
    skill that only works in combination is confounded with a main effect.
    """
    base = design.plackett_burman(11)
    folded = design.foldover(base)

    # Under Resolution III the confounding is present...
    iii = any(
        abs(float((base[:, a] * base[:, b]) @ base[:, c])) > 1e-9
        for a, b in itertools.combinations(range(11), 2)
        for c in range(11)
        if c not in (a, b)
    )
    assert iii, "expected the unfolded design to alias two-factor interactions"

    # ...and after the foldover it is gone, for every triple.
    for a, b in itertools.combinations(range(11), 2):
        interaction = folded[:, a] * folded[:, b]
        for c in range(11):
            assert abs(float(interaction @ folded[:, c])) < 1e-9


def test_full_factorial_is_the_whole_cube():
    f = design.full_factorial(4)
    assert f.shape == (16, 4)
    assert len({tuple(r) for r in f}) == 16


def test_full_factorial_refuses_an_absurd_budget():
    with pytest.raises(ValueError):
        design.full_factorial(20)


def test_main_effects_recover_a_planted_signal():
    d = design.screening_design(7)
    truth = np.array([0.0, 0.10, 0.0, -0.05, 0.0, 0.0, 0.0])
    # response = 0.5 * sum(effect * level); main effect is the hi-lo difference
    response = 0.5 + 0.5 * (d @ truth)
    recovered = design.main_effects(d, response)
    assert np.allclose(recovered, truth, atol=1e-9)


def test_configurations_are_named_subsets():
    d = np.array([[1, -1, 1], [-1, -1, -1]])
    configs = design.configurations(d, ["a", "b", "c"])
    assert configs[0].key == frozenset({"a", "c"})
    assert configs[1].key == frozenset()


def test_configurations_reject_a_mismatched_catalog():
    with pytest.raises(ValueError):
        design.configurations(np.ones((2, 3), dtype=int), ["a", "b"])


def test_permutation_samples_are_deterministic_given_a_seed():
    a = design.permutation_samples(6, 10, seed=7)
    b = design.permutation_samples(6, 10, seed=7)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, design.permutation_samples(6, 10, seed=8))
