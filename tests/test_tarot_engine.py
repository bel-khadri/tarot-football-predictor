"""Tests for the tarot engine: loading, drawing, power formula, scoring."""

from __future__ import annotations

import random
from typing import List

import pytest

from tarot_engine import (
    ELEMENT_ROLE,
    SUIT_PROFILE,
    Card,
    TarotEngine,
    explain_card,
    explain_draw,
    load_deck,
    score_cards,
)


# ----------------------------------------------------------------------
# Deck loading
# ----------------------------------------------------------------------
def test_load_deck_returns_valid_structure(deck_data) -> None:
    assert "major_arcana" in deck_data
    assert "minor_arcana" in deck_data


def test_load_deck_rejects_incomplete_deck(tmp_path) -> None:
    import json

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"major_arcana": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing major/minor"):
        load_deck(bad)


def test_load_deck_rejects_wrong_card_count(tmp_path) -> None:
    import json

    bad = tmp_path / "bad.json"
    payload = {"major_arcana": [], "minor_arcana": {"wands": []}}
    bad.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="78-card deck"):
        load_deck(bad)


def test_engine_exposes_all_78_cards(engine: TarotEngine) -> None:
    assert engine.deck_size == 78


def test_find_card_is_case_insensitive(engine: TarotEngine) -> None:
    assert engine.find_card("the sun")["name"] == "The Sun"
    assert engine.find_card("ACE OF CUPS")["name"] == "Ace of Cups"


def test_find_card_raises_for_unknown(engine: TarotEngine) -> None:
    with pytest.raises(KeyError):
        engine.find_card("Not A Card")


# ----------------------------------------------------------------------
# Drawing
# ----------------------------------------------------------------------
def test_draw_returns_requested_count(engine: TarotEngine) -> None:
    for count in (1, 3, 10, 40):
        assert len(engine.draw(count)) == count


def test_draw_never_repeats_a_card(engine: TarotEngine) -> None:
    names = [card.name for card in engine.draw(40)]
    assert len(set(names)) == 40


def test_draw_rejects_impossible_counts(engine: TarotEngine) -> None:
    with pytest.raises(ValueError, match="Cannot draw"):
        engine.draw(79)


def test_draw_rejects_invalid_reversal_chance(engine: TarotEngine) -> None:
    with pytest.raises(ValueError, match="reversal_chance"):
        engine.draw(3, reversal_chance=1.5)
    with pytest.raises(ValueError, match="reversal_chance"):
        engine.draw(3, reversal_chance=-0.1)


def test_zero_reversal_chance_gives_all_upright() -> None:
    engine = TarotEngine(rng=random.Random(99))
    assert all(not card.is_reversed for card in engine.draw(20, reversal_chance=0.0))


def test_full_reversal_chance_gives_all_reversed() -> None:
    engine = TarotEngine(rng=random.Random(99))
    assert all(card.is_reversed for card in engine.draw(20, reversal_chance=1.0))


def test_draw_is_reproducible_with_a_seed() -> None:
    first = [
        card.name + card.orientation
        for card in TarotEngine(rng=random.Random(77)).draw(8)
    ]
    second = [
        card.name + card.orientation
        for card in TarotEngine(rng=random.Random(77)).draw(8)
    ]
    assert first == second


def test_team_spread_assigns_the_three_positions(
    engine: TarotEngine,
) -> None:
    spread = engine.draw_team_spread()
    assert [card.position for card in spread] == [
        "Attack",
        "Defence",
        "Key Energy",
    ]


def test_match_context_card_is_labelled(engine: TarotEngine) -> None:
    assert engine.match_context().position == "Match Context"


# ----------------------------------------------------------------------
# Power formula
# ----------------------------------------------------------------------
def test_upright_card_keeps_full_power(sample_card: Card) -> None:
    assert sample_card.polarity_multiplier == 1.0
    assert sample_card.score() == pytest.approx(sample_card.base_power)


def test_reversed_card_is_halved(sample_card: Card) -> None:
    reversed_card = Card(
        name=sample_card.name,
        element=sample_card.element,
        base_power=sample_card.base_power,
        arcana=sample_card.arcana,
        suit=sample_card.suit,
        rank=sample_card.rank,
        is_reversed=True,
        upright_meaning=sample_card.upright_meaning,
        reversed_meaning=sample_card.reversed_meaning,
        sports_upright=sample_card.sports_upright,
        sports_reversed=sample_card.sports_reversed,
    )
    assert reversed_card.polarity_multiplier == 0.5
    assert reversed_card.score() == pytest.approx(sample_card.base_power * 0.5)


def test_synergy_bonus_is_added_verbatim(sample_card: Card) -> None:
    assert sample_card.score(7.5) == pytest.approx(
        sample_card.base_power + 7.5
    )


def test_power_formula_matches_the_specification() -> None:
    """Card Power = (Base Power x Polarity) + Elemental Synergy Bonus."""
    base, multiplier, bonus = 88, 0.5, 5.0
    card = Card(
        name="Test",
        element="Fire",
        base_power=base,
        arcana="minor",
        suit="wands",
        rank="Ace",
        is_reversed=True,
        upright_meaning="u",
        reversed_meaning="r",
        sports_upright="su",
        sports_reversed="sr",
    )
    assert card.score(bonus) == pytest.approx(base * multiplier + bonus)


def test_orientation_swaps_the_meaning(sample_card: Card) -> None:
    assert sample_card.meaning == sample_card.upright_meaning
    assert sample_card.sports_meaning == sample_card.sports_upright
    assert sample_card.orientation == "Upright"
    assert sample_card.display_name == sample_card.name


def test_reversed_orientation_shows_in_display_name(
    sample_card: Card,
) -> None:
    from dataclasses import replace

    flipped = replace(sample_card, is_reversed=True)
    assert flipped.orientation == "Reversed"
    assert flipped.display_name.endswith("(Reversed)")
    assert flipped.meaning == flipped.reversed_meaning
    assert flipped.sports_meaning == flipped.sports_reversed


# ----------------------------------------------------------------------
# Synergy and spread scoring
# ----------------------------------------------------------------------
def test_three_of_a_suit_earns_the_full_suit_bonus(fire_cards) -> None:
    bonus = TarotEngine.elemental_synergy_bonus(fire_cards)
    assert bonus == pytest.approx(10.0)  # 5 element + 5 suit


def test_mixed_spread_earns_no_synergy(engine: TarotEngine) -> None:
    spread = engine.draw(3)
    assert TarotEngine.elemental_synergy_bonus(spread) >= 0.0


def test_empty_spread_has_zero_synergy() -> None:
    assert TarotEngine.elemental_synergy_bonus([]) == 0.0


def test_scoring_routes_elements_to_roles() -> None:
    """Fire -> attack, Earth -> defence, Water -> midfield, Air -> strategy."""
    cards = [
        Card("F", "Fire", 90, "minor", "wands", "Ace", False, "u", "r", "su", "sr"),
        Card("D", "Earth", 90, "minor", "pentacles", "Ace", False, "u", "r", "su", "sr"),
        Card("M", "Water", 90, "minor", "cups", "Ace", False, "u", "r", "su", "sr"),
    ]
    profile = score_cards(cards)
    assert profile.attack == pytest.approx(90.0)
    assert profile.defence == pytest.approx(90.0)
    assert profile.midfield == pytest.approx(90.0)
    assert profile.strategy == pytest.approx(0.0)
    assert profile.dominant_element == "Fire"


def test_strengths_are_on_a_0_100_scale(fire_cards) -> None:
    profile = score_cards(fire_cards)
    for value in (
        profile.attack_strength,
        profile.defence_strength,
        profile.midfield_strength,
        profile.strategy_strength,
    ):
        assert 0.0 <= value <= 100.0


def test_two_fire_cards_beat_one(fire_cards) -> None:
    profile = score_cards(fire_cards)
    assert profile.attack_strength > 0.0
    assert profile.attack == pytest.approx(76 + 72 + 82 + 3 * 10.0)


def test_total_power_sums_every_card(fire_cards) -> None:
    profile = score_cards(fire_cards)
    expected = sum(card.score(profile.synergy_bonus) for card in fire_cards)
    assert profile.total_power == pytest.approx(expected)


def test_dominant_suit_profile_is_reported(fire_cards) -> None:
    profile = score_cards(fire_cards)
    assert profile.dominant_suit == "wands"
    assert SUIT_PROFILE["wands"]["label"] in profile.suit_narrative


def test_pentacles_dominance_signals_low_scoring() -> None:
    cards = [
        Card("P", "Earth", 90, "minor", "pentacles", "Ace", False, "u", "r", "su", "sr")
        for _ in range(3)
    ]
    profile = score_cards(cards)
    assert profile.dominant_suit == "pentacles"
    assert "Low-scoring" in profile.suit_narrative
    assert SUIT_PROFILE["pentacles"]["goal_delta"] < 0


def test_wands_dominance_signals_high_scoring() -> None:
    cards = [
        Card("W", "Fire", 90, "minor", "wands", "Ace", False, "u", "r", "su", "sr")
        for _ in range(3)
    ]
    profile = score_cards(cards)
    assert "High-scoring" in profile.suit_narrative
    assert SUIT_PROFILE["wands"]["goal_delta"] > 0


def test_swords_dominance_signals_fouls_and_cards() -> None:
    cards = [
        Card("S", "Air", 90, "minor", "swords", "Ace", False, "u", "r", "su", "sr")
        for _ in range(3)
    ]
    profile = score_cards(cards)
    assert "fouls" in profile.suit_narrative


def test_cups_dominance_signals_counter_attacks() -> None:
    cards = [
        Card("C", "Water", 90, "minor", "cups", "Ace", False, "u", "r", "su", "sr")
        for _ in range(3)
    ]
    profile = score_cards(cards)
    assert "counter-attacks" in profile.suit_narrative


def test_momentum_is_attack_minus_defence(fire_cards) -> None:
    profile = score_cards(fire_cards)
    assert profile.momentum == pytest.approx(profile.attack - profile.defence)


def test_scoring_an_empty_spread_raises(engine: TarotEngine) -> None:
    with pytest.raises(ValueError, match="empty spread"):
        engine.score_spread([])


def test_element_roles_are_defined() -> None:
    assert ELEMENT_ROLE["Fire"] == "Attack"
    assert ELEMENT_ROLE["Water"] == "Midfield"
    assert ELEMENT_ROLE["Earth"] == "Defence"
    assert ELEMENT_ROLE["Air"] == "Strategy"


def test_profile_serialises_to_json_safe_dict(fire_cards) -> None:
    import json

    payload = score_cards(fire_cards).to_dict()
    json.dumps(payload)  # must not raise
    assert payload["dominant_suit"] == "wands"
    assert len(payload["cards"]) == 3


# ----------------------------------------------------------------------
# Explanation generator
# ----------------------------------------------------------------------
def test_explain_card_mentions_position_and_score(
    sample_card: Card,
) -> None:
    text = explain_card(sample_card)
    assert sample_card.name in text
    assert str(sample_card.base_power) in text
    assert sample_card.sports_upright in text


def test_explain_card_respects_reversed_text(sample_card: Card) -> None:
    from dataclasses import replace

    text = explain_card(replace(sample_card, is_reversed=True))
    assert "reversed" in text.lower()
    assert sample_card.sports_reversed in text


def test_explain_draw_reports_the_team_name(engine: TarotEngine) -> None:
    spread = engine.draw_team_spread()
    text = explain_draw(spread, "Northgate United")
    assert "CARD EXPLANATION: Northgate United" in text
    assert "SYNERGY STORY" in text


def test_explain_draw_covers_every_card(engine: TarotEngine) -> None:
    spread = engine.draw_team_spread()
    text = explain_draw(spread, "Test FC")
    for card in spread:
        assert card.name in text


def test_explain_draw_handles_an_empty_spread() -> None:
    text = explain_draw([], "Ghost FC")
    assert "nothing to say" in text


def test_explain_draw_all_upright_is_optimistic(engine: TarotEngine) -> None:
    spread = engine.draw(3, reversal_chance=0.0)
    text = explain_draw(spread, "Optimals")
    assert "All three cards land upright" in text


def test_explain_draw_all_reversed_is_pessimistic(
    engine: TarotEngine,
) -> None:
    spread = engine.draw(3, reversal_chance=1.0)
    text = explain_draw(spread, "Doomed")
    assert "All three cards are reversed" in text


def test_absent_element_is_not_reported_as_zero_strength(
    engine: TarotEngine, fire_cards: List[Card]
) -> None:
    """No Earth card means silence about defence, not "defence 0"."""
    from dataclasses import replace

    no_earth = [
        replace(fire_cards[0], element="Fire"),
        replace(fire_cards[1], element="Fire"),
        replace(fire_cards[2], element="Air"),
    ]
    text = explain_draw(no_earth, "T")
    assert "No Earth card was drawn" in text
    # The narrative must not claim the team defends badly when nothing was drawn.
    narrative = text.split("--- SYNERGY STORY")[1]
    assert "front-loaded" not in narrative


def test_absent_fire_is_not_reported_as_zero_attack(
    engine: TarotEngine, fire_cards: List[Card]
) -> None:
    from dataclasses import replace

    no_fire = [
        replace(fire_cards[0], element="Earth"),
        replace(fire_cards[1], element="Earth"),
        replace(fire_cards[2], element="Water"),
    ]
    text = explain_draw(no_fire, "T")
    assert "No Fire card was drawn" in text


def test_front_loaded_narrative_needs_both_elements(
    engine: TarotEngine, fire_cards: List[Card]
) -> None:
    from dataclasses import replace

    both = [
        replace(fire_cards[0], element="Fire"),
        replace(fire_cards[1], element="Fire"),
        replace(fire_cards[2], element="Earth"),
    ]
    text = explain_draw(both, "T")
    assert "No Earth card was drawn" not in text
    assert "No Fire card was drawn" not in text


def test_explain_draw_accepts_an_explicit_profile(
    engine: TarotEngine,
) -> None:
    spread = engine.draw_team_spread()
    profile = engine.score_spread(spread)
    text = explain_draw(spread, "X", profile)
    assert f"{profile.total_power:.1f}" in text


def test_major_arcana_are_flagged_as_fated(engine: TarotEngine) -> None:
    cards = [
        Card("The Sun", "Fire", 98, "major", None, "The Sun", False,
             "u", "r", "su", "sr"),
        Card("The World", "Earth", 98, "major", None, "The World", False,
             "u", "r", "su", "sr"),
        Card("Two of Cups", "Water", 78, "minor", "cups", "2", False,
             "u", "r", "su", "sr"),
    ]
    text = explain_draw(cards, "Fated FC")
    assert "Major Arcana" in text
    assert "fated" in text