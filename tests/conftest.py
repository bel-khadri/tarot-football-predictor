"""Shared pytest fixtures."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, List

import pytest

from tarot_engine import Card, TarotEngine

DECK_PATH = Path(__file__).resolve().parents[1] / "tarot_deck.json"


@pytest.fixture()
def deck_data() -> Dict[str, Any]:
    import json

    with open(DECK_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture()
def engine() -> TarotEngine:
    """Deterministic engine so tests never flake."""
    return TarotEngine(rng=random.Random(1234))


@pytest.fixture()
def sample_card(deck_data: Dict[str, Any]) -> Card:
    """The Sun, upright."""
    raw = next(c for c in deck_data["major_arcana"] if c["name"] == "The Sun")
    return Card(
        name=raw["name"],
        element=raw["element"],
        base_power=raw["base_power"],
        arcana=raw["arcana"],
        suit=raw.get("suit"),
        rank=raw.get("rank", raw["name"]),
        is_reversed=False,
        upright_meaning=raw["upright_meaning"],
        reversed_meaning=raw["reversed_meaning"],
        sports_upright=raw["sports_upright"],
        sports_reversed=raw["sports_reversed"],
    )


@pytest.fixture()
def fire_cards() -> List[Card]:
    """Three Fire cards, all upright, same suit - maximum synergy."""
    names = [("Two of Wands", 76), ("Four of Wands", 72), ("Six of Wands", 82)]
    return [
        Card(
            name=name,
            element="Fire",
            base_power=power,
            arcana="minor",
            suit="wands",
            rank=name.split(" of ")[0],
            is_reversed=False,
            upright_meaning="u",
            reversed_meaning="r",
            sports_upright="su",
            sports_reversed="sr",
            position=position,
        )
        for (name, power), position in zip(names, ("Attack", "Defence", "Key Energy"))
    ]