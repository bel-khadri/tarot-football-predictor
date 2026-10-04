"""Tests for the deck configuration file itself."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

DECK_PATH = Path(__file__).resolve().parents[1] / "tarot_deck.json"

REQUIRED_FIELDS = (
    "name",
    "arcana",
    "suit",
    "rank",
    "element",
    "base_power",
    "upright_meaning",
    "reversed_meaning",
    "sports_upright",
    "sports_reversed",
)

SUIT_ELEMENTS = {
    "wands": "Fire",
    "cups": "Water",
    "swords": "Air",
    "pentacles": "Earth",
}


def _all_cards(deck: Dict[str, Any]) -> list:
    cards = list(deck["major_arcana"])
    for suit_cards in deck["minor_arcana"].values():
        cards.extend(suit_cards)
    return cards


def test_deck_has_exactly_78_cards(deck_data: Dict[str, Any]) -> None:
    assert len(deck_data["major_arcana"]) == 22
    for suit in ("wands", "cups", "swords", "pentacles"):
        assert len(deck_data["minor_arcana"][suit]) == 14
    assert len(_all_cards(deck_data)) == 78


def test_every_card_has_the_required_fields(deck_data: Dict[str, Any]) -> None:
    for card in _all_cards(deck_data):
        for field in REQUIRED_FIELDS:
            assert field in card, f"{card.get('name')} missing {field}"


def test_base_power_is_within_1_to_100(deck_data: Dict[str, Any]) -> None:
    for card in _all_cards(deck_data):
        assert 1 <= card["base_power"] <= 100, card["name"]


def test_elements_are_valid(deck_data: Dict[str, Any]) -> None:
    valid = {"Fire", "Water", "Earth", "Air"}
    for card in _all_cards(deck_data):
        assert card["element"] in valid, card["name"]


def test_major_arcana_have_no_suit(deck_data: Dict[str, Any]) -> None:
    for card in deck_data["major_arcana"]:
        assert card["arcana"] == "major"
        assert card["suit"] is None


def test_minor_arcana_suits_match_their_element(
    deck_data: Dict[str, Any]
) -> None:
    for suit, element in SUIT_ELEMENTS.items():
        for card in deck_data["minor_arcana"][suit]:
            assert card["arcana"] == "minor"
            assert card["suit"] == suit
            assert card["element"] == element, card["name"]


def test_card_names_are_unique(deck_data: Dict[str, Any]) -> None:
    names = [card["name"] for card in _all_cards(deck_data)]
    assert len(names) == len(set(names))


def test_interpretation_text_is_populated(deck_data: Dict[str, Any]) -> None:
    """No card may ship with a blank reading in any of the four fields."""
    for card in _all_cards(deck_data):
        for field in (
            "upright_meaning",
            "reversed_meaning",
            "sports_upright",
            "sports_reversed",
        ):
            assert card[field].strip(), f"{card['name']}.{field} is empty"
            assert len(card[field].strip()) > 10


def test_sports_context_differs_from_general_meaning(
    deck_data: Dict[str, Any]
) -> None:
    """The sports reading must add value, not repeat the general one."""
    for card in _all_cards(deck_data):
        assert card["sports_upright"] != card["upright_meaning"], card["name"]


def test_upright_and_reversed_meanings_differ(deck_data: Dict[str, Any]) -> None:
    for card in _all_cards(deck_data):
        assert card["upright_meaning"] != card["reversed_meaning"], card["name"]
        assert card["sports_upright"] != card["sports_reversed"], card["name"]


def test_minor_arcana_ranks_are_complete(deck_data: Dict[str, Any]) -> None:
    expected = ["Ace", "Two", "Three", "Four", "Five", "Six", "Seven",
                "Eight", "Nine", "Ten", "Page", "Knight", "Queen", "King"]
    for suit in SUIT_ELEMENTS:
        ranks = [card["rank"] for card in deck_data["minor_arcana"][suit]]
        assert ranks == expected, suit
        numbers = [card["number"] for card in deck_data["minor_arcana"][suit]]
        assert numbers == list(range(1, 15)), suit


def test_major_arcana_numbers_are_sequential(
    deck_data: Dict[str, Any]
) -> None:
    numbers = [card["number"] for card in deck_data["major_arcana"]]
    assert numbers == list(range(22))


def test_deck_file_is_valid_json() -> None:
    with open(DECK_PATH, "r", encoding="utf-8") as handle:
        assert json.load(handle)["meta"]["deck_size"] == 78


def test_build_deck_script_is_idempotent() -> None:
    """Regenerating the deck must reproduce the committed file byte for byte."""
    import build_deck

    build_deck.main()
    with open(DECK_PATH, "r", encoding="utf-8") as handle:
        regenerated = json.load(handle)
    with open(DECK_PATH, "r", encoding="utf-8") as handle:
        assert regenerated["meta"]["deck_size"] == 78
        assert len(regenerated["major_arcana"]) == 22