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


def test_interaction_index_recovers_pure_synergy():
    """v(a)=v(b)=0, v(ab)=1: the pair is worth 1 that neither is worth alone."""
    players = ["a", "b"]
    values = _table(lambda c: 1.0 if len(c) == 2 else 0.0, players)
    interaction = estimate.interaction_index_by_task(values, players).mean(axis=2)
    assert interaction[0, 1] == pytest.approx(1.0)
    assert interaction[1, 0] == pytest.approx(1.0)
    assert interaction[0, 0] == 0.0


def test_interaction_index_is_negative_for_substitutes():
    """Two skills that do the same job: stacking them buys nothing."""
    players = ["a", "b"]
    values = _table(lambda c: 1.0 if c else 0.0, players)
    interaction = estimate.interaction_index_by_task(values, players).mean(axis=2)
    assert interaction[0, 1] == pytest.approx(-1.0)


def test_interaction_index_is_zero_for_an_additive_catalog():
    players = ["a", "b", "c"]
    weights = {"a": 0.3, "b": 0.1, "c": -0.2}
    values = _table(lambda c: sum(weights[p] for p in c), players)
    interaction = estimate.interaction_index_by_task(values, players).mean(axis=2)
    assert np.allclose(interaction, 0.0, atol=1e-12)


def test_the_literal_question_skill_1_with_3_versus_1_with_2():
    """Is s1 better paired with s3 than with s2? Answered with an interval."""
    rng = np.random.default_rng(11)
    n_tasks = 300
    players = ["s1", "s2", "s3"]
    base = {p: 0.0 for p in players}
    def value(coalition):
        v = 0.1 * len(coalition)
        if {"s1", "s3"} <= coalition:
            v += 0.25          # s1 and s3 are complements
        if {"s1", "s2"} <= coalition:
            v -= 0.05          # s1 and s2 get in each other's way
        return v
    values = {
        frozenset(c): value(frozenset(c)) + rng.normal(0, 0.05, n_tasks)
        for s in range(4)
        for c in itertools.combinations(players, s)
    }
    better = estimate.compare_coalitions(values, ["s1", "s3"], ["s1", "s2"], seed=2)
    assert better.point > 0
    assert better.excludes_zero

    interaction = estimate.interaction_index_by_task(values, players).mean(axis=2)
    assert interaction[0, 2] > 0.2      # s1 x s3 synergy
    assert interaction[0, 1] < 0        # s1 x s2 redundancy


def test_best_coalitions_answers_the_budget_question():
    players = ["a", "b", "c"]
    weights = {"a": 0.3, "b": 0.2, "c": 0.05}
    values = _table(lambda c: sum(weights[p] for p in c), players, n_tasks=3)
    top_pairs = estimate.best_coalitions(values, size=2, top=3)
    assert top_pairs[0][0] == ("a", "b")
    assert len(estimate.best_coalitions(values, size=1)) == 3


def test_compare_coalitions_refuses_an_unrun_combination():
    players = ["a", "b"]
    values = _table(lambda c: float(len(c)), players)
    with pytest.raises(KeyError, match="never run"):
        estimate.compare_coalitions(values, ["a", "b", "z"], ["a"])


def _block_interaction(groups, independents, strength):
    """Interaction matrix: every pair inside a group is redundant at -strength."""
    skills = [s for g in groups for s in g] + list(independents)
    index = {s: i for i, s in enumerate(skills)}
    m = np.zeros((len(skills), len(skills)))
    for group in groups:
        for a, b in itertools.combinations(group, 2):
            m[index[a], index[b]] = m[index[b], index[a]] = -strength
    return skills, m


def test_redundancy_axes_recover_a_planted_block():
    """Three mutually redundant skills must land on one axis, same sign.

    The algebra is exact: a block of m skills interacting pairwise at -c has an
    eigenvalue of -c(m-1) whose eigenvector is uniform over the block.
    """
    skills, matrix = _block_interaction([("a", "b", "c")], ["d", "e"], strength=0.1)
    structure = estimate.redundancy_axes(matrix, skills)
    assert structure.clusters == (("a", "b", "c"),)
    assert set(structure.unclustered) == {"d", "e"}
    assert structure.eigenvalues[0] == pytest.approx(-0.1 * (3 - 1))


def test_redundancy_axes_separate_two_independent_blocks():
    skills, matrix = _block_interaction([("a", "b"), ("c", "d")], ["e"], strength=0.2)
    structure = estimate.redundancy_axes(matrix, skills)
    found = {frozenset(c) for c in structure.clusters}
    assert found == {frozenset({"a", "b"}), frozenset({"c", "d"})}
    assert structure.unclustered == ("e",)


def test_an_additive_catalog_has_no_redundancy_areas():
    skills = ["a", "b", "c"]
    structure = estimate.redundancy_axes(np.zeros((3, 3)), skills)
    assert structure.clusters == ()
    assert structure.unclustered == ("a", "b", "c")


def test_minimal_spanning_subset_keeps_one_per_area_and_drops_the_useless():
    skills, matrix = _block_interaction([("a", "b", "c")], ["d", "e"], strength=0.1)
    structure = estimate.redundancy_axes(matrix, skills)
    phi = {"a": 0.02, "b": 0.09, "c": 0.05, "d": 0.04, "e": -0.01}
    assert estimate.minimal_spanning_subset(structure, phi) == ("b", "d")


def test_redundancy_axes_reject_an_asymmetric_matrix():
    with pytest.raises(ValueError, match="symmetric"):
        estimate.redundancy_axes(np.array([[0.0, 1.0], [2.0, 0.0]]), ["a", "b"])


def test_general_interaction_index_reproduces_the_shapley_value_at_order_one():
    """The general index must contain the special cases, not merely resemble them."""
    rng = np.random.default_rng(21)
    players = ["a", "b", "c", "d"]
    values = {
        frozenset(c): rng.normal(size=3)
        for s in range(5)
        for c in itertools.combinations(players, s)
    }
    phi = estimate.shapley_exact_by_task(values, players)
    for i, p in enumerate(players):
        general = estimate.interaction_index(values, players, [p])
        assert np.allclose(general, phi[i], atol=1e-12)


def test_general_interaction_index_reproduces_the_pairwise_index_at_order_two():
    rng = np.random.default_rng(22)
    players = ["a", "b", "c", "d"]
    values = {
        frozenset(c): rng.normal(size=3)
        for s in range(5)
        for c in itertools.combinations(players, s)
    }
    pairwise = estimate.interaction_index_by_task(values, players)
    for i, j in itertools.combinations(range(4), 2):
        general = estimate.interaction_index(values, players, [players[i], players[j]])
        assert np.allclose(general, pairwise[i, j], atol=1e-12)


def test_third_order_interaction_is_detected_where_pairs_show_nothing():
    """A trio that only works all together: every pair reads zero, the triple does not."""
    players = ["a", "b", "c"]
    values = _table(lambda c: 1.0 if len(c) == 3 else 0.0, players)
    for pair in itertools.combinations(players, 2):
        assert estimate.interaction_index(values, players, list(pair)).mean() != pytest.approx(0.0)
    triple = estimate.interaction_index(values, players, players).mean()
    assert triple == pytest.approx(1.0)


def test_coalition_curve_flattens_where_the_catalog_stops_paying():
    players = ["a", "b", "c", "d"]
    # a and b are real; c and d duplicate a and buy nothing on top of it.
    def value(coalition):
        v = 0.0
        if "a" in coalition or "c" in coalition or "d" in coalition:
            v += 0.30
        if "b" in coalition:
            v += 0.10
        return v
    values = _table(lambda c: value(c), players, n_tasks=5)
    phi = {p: float(v) for p, v in zip(players, estimate.shapley_exact_by_task(values, players).mean(axis=1))}
    curve = estimate.coalition_curve(values, phi)
    assert curve.sizes == (0, 1, 2, 3, 4)
    assert curve.best_value[2] == pytest.approx(0.40)
    assert curve.best_value[3] == pytest.approx(0.40)   # the third skill adds nothing
    # Redundancy shows as a positive gap in the middle: Shapley splits credit
    # among substitutes, so any one of them beats its own share.
    assert curve.gap[1] > 0
    # And the gap must vanish at both ends, by the efficiency property.
    assert curve.gap[0] == pytest.approx(0.0)
    assert curve.gap[-1] == pytest.approx(0.0)


def test_coalition_curve_shows_complementarity_as_a_negative_gap():
    """Two skills worth nothing apart and everything together."""
    players = ["a", "b"]
    values = _table(lambda c: 1.0 if len(c) == 2 else 0.0, players, n_tasks=4)
    phi = {p: float(v) for p, v in zip(players, estimate.shapley_exact_by_task(values, players).mean(axis=1))}
    curve = estimate.coalition_curve(values, phi)
    assert curve.gap[1] < 0          # one alone falls short of its attributed share
    assert curve.gap[-1] == pytest.approx(0.0)


def test_interaction_index_rejects_an_unknown_player():
    players = ["a", "b"]
    values = _table(lambda c: float(len(c)), players)
    with pytest.raises(ValueError, match="not players"):
        estimate.interaction_index(values, players, ["a", "z"])
