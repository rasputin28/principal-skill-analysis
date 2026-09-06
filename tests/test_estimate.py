import itertools

import numpy as np
import pytest

from psa import estimate


def _table(fn, players, n_tasks=1):
    out = {}
    for size in range(len(players) + 1):
        for combo in itertools.combinations(players, size):
            out[frozenset(combo)] = np.full(n_tasks, fn(frozenset(combo)))
    return out


def test_efficiency_holds_for_an_arbitrary_game():
    rng = np.random.default_rng(0)
    players = ["a", "b", "c", "d"]
    payoff = {frozenset(c): rng.normal() for s in range(5) for c in itertools.combinations(players, s)}
    payoff[frozenset()] = 0.0
    values = {k: np.array([v]) for k, v in payoff.items()}
    phi = estimate.shapley_exact_by_task(values, players)
    assert estimate.efficiency_residual(phi, values, players) < 1e-12


def test_null_player_gets_exactly_zero():
    players = ["useful", "inert"]
    values = _table(lambda c: 1.0 if "useful" in c else 0.0, players)
    phi = estimate.shapley_exact_by_task(values, players)
    assert phi[players.index("inert")].mean() == pytest.approx(0.0, abs=1e-12)
    assert phi[players.index("useful")].mean() == pytest.approx(1.0)


def test_pure_interaction_is_split_evenly_and_ablation_would_miss_it():
    """v(a)=v(b)=0 but v(ab)=1: neither skill works alone.

    Shapley gives each 0.5. This is hypothesis H3 of the paper made concrete,
    and the reason leave-one-out ablation is insufficient.
    """
    players = ["a", "b"]
    values = _table(lambda c: 1.0 if len(c) == 2 else 0.0, players)
    phi = estimate.shapley_exact_by_task(values, players)
    assert phi.mean(axis=1) == pytest.approx([0.5, 0.5])


def test_symmetric_players_receive_equal_credit():
    players = ["a", "b", "c"]
    values = _table(lambda c: float(len(c)) ** 2, players)
    phi = estimate.shapley_exact_by_task(values, players).mean(axis=1)
    assert phi[0] == pytest.approx(phi[1]) == pytest.approx(phi[2])


def test_exact_shapley_refuses_an_incomplete_table():
    players = ["a", "b", "c"]
    values = _table(lambda c: float(len(c)), players)
    values.pop(frozenset({"a"}))
    with pytest.raises(ValueError, match="all 8 subsets"):
        estimate.shapley_exact_by_task(values, players)


def test_sampling_estimator_approaches_the_exact_one():
    from psa import design as design_mod

    rng = np.random.default_rng(1)
    players = ["a", "b", "c", "d", "e"]
    weights = dict(zip(players, [0.3, 0.2, 0.0, -0.1, 0.05]))
    values = _table(lambda c: sum(weights[p] for p in c), players)
    exact = estimate.shapley_exact_by_task(values, players).mean(axis=1)
    perms = design_mod.permutation_samples(len(players), 400, seed=3)
    sampled = estimate.shapley_sampling_by_task(values, players, perms).mean(axis=1)
    assert np.allclose(exact, sampled, atol=1e-9)  # additive game: exact for any order


def test_bootstrap_interval_brackets_the_point_estimate():
    rng = np.random.default_rng(2)
    players = ["a", "b"]
    n_tasks = 200
    values = {
        frozenset(): np.zeros(n_tasks),
        frozenset({"a"}): rng.normal(0.2, 0.1, n_tasks),
        frozenset({"b"}): rng.normal(0.0, 0.1, n_tasks),
        frozenset({"a", "b"}): rng.normal(0.2, 0.1, n_tasks),
    }
    phi = estimate.shapley_exact_by_task(values, players)
    ci = estimate.bootstrap_ci(phi, players, n_boot=500, seed=5)
    assert ci["a"].low <= ci["a"].point <= ci["a"].high
    assert ci["a"].excludes_zero
    assert not ci["b"].excludes_zero


def test_latent_axes_attribute_an_axis_to_the_skill_that_drives_it():
    """Half the tasks respond only to skill 'x'; the axis must load on 'x'."""
    skills = ["x", "y"]
    skill_matrix = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
    n_tasks = 40
    outcomes = np.zeros((n_tasks, 4))
    outcomes[: n_tasks // 2] = skill_matrix[:, 0]          # x-sensitive tasks
    outcomes[n_tasks // 2 :] = 1.0                          # insensitive tasks
    axes = estimate.latent_axes(outcomes, skill_matrix, skills, n_components=2)
    assert abs(axes.skill_loadings[0, 0]) > abs(axes.skill_loadings[1, 0])
    assert axes.explained_variance_ratio[0] > 0.9


def test_rank_agreement_is_one_for_identical_orderings():
    a = {"p": 1.0, "q": 0.5, "r": 0.0}
    assert estimate.rank_agreement(a, a) == pytest.approx(1.0)
    flipped = {"p": 0.0, "q": 0.5, "r": 1.0}
    assert estimate.rank_agreement(a, flipped) == pytest.approx(-1.0)
