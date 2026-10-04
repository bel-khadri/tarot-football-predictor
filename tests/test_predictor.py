"""Tests for the predictor: goal model, ranges, verdicts and end-to-end runs."""

from __future__ import annotations

import json
import random

import pytest

from predictor import Predictor
from tarot_engine import TarotEngine

MATCH_DATE = "2026-10-04"


@pytest.fixture()
def predictor() -> Predictor:
    return Predictor(rng=random.Random(20261004))


# ----------------------------------------------------------------------
# Numerology analysis
# ----------------------------------------------------------------------
def test_analyse_numerology_returns_a_full_reading(
    predictor: Predictor,
) -> None:
    reading = predictor.analyse_numerology("Arsenal", "Chelsea", MATCH_DATE)
    assert reading.life_path == 6
    assert reading.team_a_expression > 0
    assert reading.team_b_expression > 0
    assert reading.team_a_chaldean > 0
    assert reading.team_b_chaldean > 0
    assert 0 <= reading.team_a_compatibility <= 100
    assert 0 <= reading.team_b_compatibility <= 100
    assert reading.narrative.strip()
    assert reading.winner in {"Arsenal", "Chelsea", "Draw"}


def test_numerology_narrative_names_both_teams(
    predictor: Predictor,
) -> None:
    reading = predictor.analyse_numerology("Arsenal", "Chelsea", MATCH_DATE)
    assert "Arsenal" in reading.narrative
    assert "Chelsea" in reading.narrative


def test_numerology_goal_bias_is_bounded(predictor: Predictor) -> None:
    for a, b in (
        ("Arsenal", "Chelsea"),
        ("Inter", "Milan"),
        ("Real Madrid", "Barcelona"),
        ("Brazil", "Argentina"),
    ):
        reading = predictor.analyse_numerology(a, b, MATCH_DATE)
        assert -0.6 <= reading.goal_bias <= 0.6


def test_numerology_probabilities_sum_to_100(
    predictor: Predictor,
) -> None:
    reading = predictor.analyse_numerology("Arsenal", "Chelsea", MATCH_DATE)
    assert reading.draw_probability + reading.winner_probability == pytest.approx(
        100.0, abs=0.11
    )


def test_identical_names_are_numerologically_level(
    predictor: Predictor,
) -> None:
    reading = predictor.analyse_numerology("United", "United", MATCH_DATE)
    assert reading.winner == "Draw"


# ----------------------------------------------------------------------
# Goal model
# ----------------------------------------------------------------------
def test_goal_expectation_uses_attack_and_opponent_defence(
    predictor: Predictor,
) -> None:
    cards_a = predictor.tarot.draw(3, reversal_chance=0.0)
    cards_b = predictor.tarot.draw(3, reversal_chance=0.0)
    profile_a = predictor.tarot.score_spread(cards_a)
    profile_b = predictor.tarot.score_spread(cards_b)
    goals, basis = predictor.goal_expectation(profile_a, profile_b)
    assert goals > 0
    assert "base" in basis


def test_weak_attack_lowers_the_goal_line(predictor: Predictor) -> None:
    from tarot_engine import Card

    hot = [
        Card("W", "Fire", 98, "minor", "wands", "Ace", False, "u", "r", "su", "sr")
        for _ in range(3)
    ]
    cold = [
        Card("P", "Earth", 98, "minor", "pentacles", "Ace", False,
             "u", "r", "su", "sr")
        for _ in range(3)
    ]
    hot_profile = predictor.tarot.score_spread(hot)
    cold_profile = predictor.tarot.score_spread(cold)
    hot_goals, _ = predictor.goal_expectation(hot_profile, cold_profile)
    cold_goals, _ = predictor.goal_expectation(cold_profile, hot_profile)
    assert hot_goals > cold_goals


def test_pentacles_reduce_expectations_more_than_wands(
    predictor: Predictor,
) -> None:
    from tarot_engine import Card

    def spread(element: str, suit: str) -> list:
        return [
            Card("X", element, 90, "minor", suit, "Ace", False,
                 "u", "r", "su", "sr")
            for _ in range(3)
        ]

    neutral = [
        Card("N", "Air", 90, "minor", "swords", "Ace", False, "u", "r", "su", "sr")
        for _ in range(3)
    ]
    wands_goals, _ = predictor.goal_expectation(
        predictor.tarot.score_spread(spread("Fire", "wands")),
        predictor.tarot.score_spread(neutral),
    )
    pentacles_goals, _ = predictor.goal_expectation(
        predictor.tarot.score_spread(spread("Earth", "pentacles")),
        predictor.tarot.score_spread(neutral),
    )
    assert wands_goals > pentacles_goals


def test_no_fire_card_triggers_the_cold_attack_penalty(
    predictor: Predictor,
) -> None:
    from tarot_engine import Card

    no_fire = [
        Card("P", "Earth", 90, "minor", "pentacles", "Ace", False,
             "u", "r", "su", "sr")
        for _ in range(3)
    ]
    goals, basis = predictor.goal_expectation(
        predictor.tarot.score_spread(no_fire),
        predictor.tarot.score_spread(no_fire),
    )
    assert "No Fire card" in basis
    assert goals > 0


def test_goal_range_is_ordered_and_sane(predictor: Predictor) -> None:
    for expected in (0.2, 0.9, 1.35, 2.0, 3.4, 5.0):
        primary, low, high = predictor.goal_range(expected)
        assert 0 <= low <= primary <= high
        assert high - primary <= 2


def test_finalise_range_is_plausible(predictor: Predictor) -> None:
    assert predictor._finalise_range(0, False) == (0, 1)
    assert predictor._finalise_range(1, False) == (0, 2)
    assert predictor._finalise_range(3, True) == (2, 5)
    assert predictor._finalise_range(3, False) == (1, 4)


# ----------------------------------------------------------------------
# Verdict logic
# ----------------------------------------------------------------------
def test_draw_is_called_when_scores_are_level() -> None:
    assert Predictor._decide_winner("A", "B", 50.0, 50.0) == "Draw"
    assert Predictor._decide_winner("A", "B", 52.0, 50.5) == "Draw"


def test_higher_score_wins() -> None:
    assert Predictor._decide_winner("A", "B", 60.0, 40.0) == "A"
    assert Predictor._decide_winner("A", "B", 40.0, 60.0) == "B"


def test_agreeing_systems_keep_their_winner() -> None:
    from tarot_engine import Card

    match_card = Card("M", "Fire", 90, "major", None, "M", False,
                      "u", "r", "su", "sr")
    assert Predictor._consensus("A", "B", 60.0, 40.0, "A", "A", match_card) == "A"
    assert Predictor._consensus("A", "B", 40.0, 60.0, "B", "B", match_card) == "B"


def test_disagreeing_systems_fall_back_to_the_card_score() -> None:
    from tarot_engine import Card

    match_card = Card("M", "Fire", 90, "major", None, "M", False,
                      "u", "r", "su", "sr")
    assert Predictor._consensus("A", "B", 60.0, 40.0, "A", "B", match_card) == "A"


def test_disagreement_on_a_level_score_is_a_draw() -> None:
    from tarot_engine import Card

    match_card = Card("M", "Fire", 90, "major", None, "M", False,
                      "u", "r", "su", "sr")
    assert Predictor._consensus("A", "B", 50.0, 50.5, "A", "B", match_card) == "Draw"


def test_reversed_match_card_forces_a_draw() -> None:
    from tarot_engine import Card

    match_card = Card("M", "Fire", 90, "major", None, "M", True,
                      "u", "r", "su", "sr")
    assert Predictor._consensus("A", "B", 70.0, 30.0, "A", "B", match_card) == "Draw"


def test_winner_lean_matches_the_verdict() -> None:
    assert Predictor._apply_winner_lean(1, 1, "A", "A", "B") == (2, 1)
    assert Predictor._apply_winner_lean(2, 1, "A", "A", "B") == (2, 1)
    assert Predictor._apply_winner_lean(2, 1, "B", "A", "B") == (2, 3)
    assert Predictor._apply_winner_lean(1, 2, "B", "A", "B") == (1, 2)


def test_winner_lean_evens_a_draw() -> None:
    assert Predictor._apply_winner_lean(2, 1, "Draw", "A", "B") == (2, 2)


# ----------------------------------------------------------------------
# End to end
# ----------------------------------------------------------------------
def test_predict_returns_a_complete_reading(predictor: Predictor) -> None:
    result = predictor.predict("Arsenal", "Chelsea", MATCH_DATE)
    assert result.team_a == "Arsenal"
    assert result.team_b == "Chelsea"
    assert result.match_date == MATCH_DATE
    assert len(result.reading_a.cards) == 3
    assert len(result.reading_b.cards) == 3
    assert result.match_card is not None
    assert result.consensus_winner in {"Arsenal", "Chelsea", "Draw"}


def test_predict_produces_a_coherent_scoreline(
    predictor: Predictor,
) -> None:
    result = predictor.predict("Arsenal", "Chelsea", MATCH_DATE)
    assert result.predicted_goals_a >= 0
    assert result.predicted_goals_b >= 0
    if result.consensus_winner == "Arsenal":
        assert result.predicted_goals_a > result.predicted_goals_b
    elif result.consensus_winner == "Chelsea":
        assert result.predicted_goals_b > result.predicted_goals_a
    else:
        assert result.predicted_goals_a == result.predicted_goals_b


def test_goal_range_contains_the_primary_count(
    predictor: Predictor,
) -> None:
    result = predictor.predict("Arsenal", "Chelsea", MATCH_DATE)
    for reading in (result.reading_a, result.reading_b):
        low, high = reading.goal_range
        assert low <= reading.primary_goals <= high


def test_both_teams_get_the_same_goal_count_cap(predictor: Predictor) -> None:
    result = predictor.predict("Inter", "Milan", MATCH_DATE)
    for reading in (result.reading_a, result.reading_b):
        assert reading.goal_range[1] - reading.primary_goals <= 2


def test_readings_include_the_full_explanation(
    predictor: Predictor,
) -> None:
    result = predictor.predict("Arsenal", "Chelsea", MATCH_DATE)
    for reading in (result.reading_a, result.reading_b):
        assert "CARD EXPLANATION" in reading.explanation
        assert "SYNERGY STORY" in reading.explanation
        assert reading.name in reading.explanation


def test_predict_is_reproducible_with_a_seed() -> None:
    first = Predictor(rng=random.Random(5)).predict("A FC", "B FC", MATCH_DATE)
    second = Predictor(rng=random.Random(5)).predict("A FC", "B FC", MATCH_DATE)
    assert [c.display_name for c in first.reading_a.cards] == [
        c.display_name for c in second.reading_a.cards
    ]
    assert first.predicted_goals_a == second.predicted_goals_a


def test_predict_defaults_to_today(predictor: Predictor) -> None:
    from datetime import date

    result = predictor.predict("Home", "Away")
    assert result.match_date == date.today().isoformat()


def test_predict_rejects_blank_team_names(predictor: Predictor) -> None:
    with pytest.raises(ValueError, match="team names"):
        predictor.predict("   ", "Chelsea", MATCH_DATE)
    with pytest.raises(ValueError, match="team names"):
        predictor.predict("Arsenal", "", MATCH_DATE)


def test_predict_rejects_a_malformed_date(predictor: Predictor) -> None:
    with pytest.raises(ValueError):
        predictor.predict("Arsenal", "Chelsea", "10/04/2026")


def test_scores_stay_on_the_0_100_scale(predictor: Predictor) -> None:
    result = predictor.predict("Arsenal", "Chelsea", MATCH_DATE)
    assert 0.0 <= result.score_a <= 100.0
    assert 0.0 <= result.score_b <= 100.0


def test_confidence_equals_the_score_gap(predictor: Predictor) -> None:
    result = predictor.predict("Arsenal", "Chelsea", MATCH_DATE)
    assert result.confidence == pytest.approx(abs(result.score_a - result.score_b))


def test_probabilities_are_bounded(predictor: Predictor) -> None:
    result = predictor.predict("Arsenal", "Chelsea", MATCH_DATE)
    assert 0.0 <= result.draw_probability <= 100.0
    assert 0.0 <= result.winner_probability <= 100.0


def test_verdict_reasoning_mentions_the_consensus(
    predictor: Predictor,
) -> None:
    result = predictor.predict("Arsenal", "Chelsea", MATCH_DATE)
    assert result.verdict_reasoning.strip()
    if result.consensus_winner == "Draw":
        assert "DRAW" in result.verdict_reasoning.upper()
    else:
        assert result.consensus_winner.upper() in result.verdict_reasoning.upper()


def test_prediction_serialises_to_json(predictor: Predictor) -> None:
    payload = predictor.predict("Arsenal", "Chelsea", MATCH_DATE).to_dict()
    encoded = json.dumps(payload)
    assert json.loads(encoded)["team_a"] == "Arsenal"


def test_prediction_contains_numerology_fields(
    predictor: Predictor,
) -> None:
    payload = predictor.predict("Arsenal", "Chelsea", MATCH_DATE).to_dict()
    numerology = payload["numerology"]
    for key in (
        "life_path",
        "life_path_meaning",
        "team_a_expression",
        "team_b_expression",
        "team_a_compatibility",
        "team_b_compatibility",
        "winner",
    ):
        assert key in numerology


def test_many_runs_never_produce_an_impossible_result() -> None:
    """Fuzz: no negatives, no out-of-range values, verdict always consistent."""
    predictor = Predictor(rng=random.Random(31337))
    for index in range(60):
        result = predictor.predict(f"Team A{index}", f"Team B{index}", MATCH_DATE)
        assert result.predicted_goals_a >= 0
        assert result.predicted_goals_b >= 0
        assert 0.0 <= result.score_a <= 100.0
        assert 0.0 <= result.score_b <= 100.0
        assert result.consensus_winner in {"Draw", result.team_a, result.team_b}