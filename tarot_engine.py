"""Tarot engine: deck loading, deterministic draws, power scoring and the
elemental / suit profiling that drives goal-range prediction."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

DECK_PATH = Path(__file__).parent / "tarot_deck.json"

#: Which part of the pitch each element governs.
ELEMENT_ROLE: Dict[str, str] = {
    "Fire": "Attack",
    "Water": "Midfield",
    "Earth": "Defence",
    "Air": "Strategy",
}

#: Upright cards keep full power; reversed cards are halved.
UPRIGHT_MULTIPLIER = 1.0
REVERSED_MULTIPLIER = 0.5

#: Positional spread used for a team's three-card draw.
SPREAD_POSITIONS = ("Attack", "Defence", "Key Energy")

#: Composite weights used when a team totals up its spread.
ATTACK_ELEMENTS = ("Fire",)
DEFENCE_ELEMENTS = ("Earth",)
FLOW_ELEMENTS = ("Water",)
STRATEGY_ELEMENTS = ("Air",)

#: Suit -> goal-scoring bias, from the brief.
SUIT_PROFILE: Dict[str, Dict[str, Any]] = {
    "wands": {
        "label": "Fire / Wands",
        "tempo": "High-scoring, aggressive offense",
        "goal_delta": 0.55,
        "narrative": (
            "The Wands pile into the box. This is a side that wants to score "
            "first, score often and dare the opponent to keep up."
        ),
    },
    "cups": {
        "label": "Water / Cups",
        "tempo": "Dynamic midfield play and counter-attacks",
        "goal_delta": 0.25,
        "narrative": (
            "The Cups keep the ball moving through midfield; goals arrive in "
            "waves, on the counter, whenever the opposition commits a man "
            "forward."
        ),
    },
    "swords": {
        "label": "Air / Swords",
        "tempo": "High tactical fouls, card discipline or set-piece goals",
        "goal_delta": 0.10,
        "narrative": (
            "The Swords make this a thinking, cutting game: set-pieces, "
            "defensive headers and a card count that decides how many "
            "chances even get taken."
        ),
    },
    "pentacles": {
        "label": "Earth / Pentacles",
        "tempo": "Low-scoring, strong defensive block",
        "goal_delta": -0.45,
        "narrative": (
            "The Pentacles dig in. This is a compact, unglamorous side that "
            "would rather win 1-0 on the counter than lose 3-2 in a siege."
        ),
    },
}

#: Master (Major Arcana) cards skew a spread toward decisive, eventful football.
MAJOR_EVENT_BONUS = 6.0

#: Divisor turning a raw element total into a 0-100 rating. Two strong cards
#: (~85 each plus synergy) land in the high 80s, a single card near 45.
ELEMENT_SCALE = 200.0


@dataclass(frozen=True)
class Card:
    """One drawn card with its orientation resolved."""

    name: str
    element: str
    base_power: int
    arcana: str
    suit: Optional[str]
    rank: str
    is_reversed: bool
    upright_meaning: str
    reversed_meaning: str
    sports_upright: str
    sports_reversed: str
    position: Optional[str] = None

    # -- orientation ---------------------------------------------------
    @property
    def orientation(self) -> str:
        return "Reversed" if self.is_reversed else "Upright"

    @property
    def display_name(self) -> str:
        return f"{self.name} (Reversed)" if self.is_reversed else self.name

    @property
    def role(self) -> str:
        return ELEMENT_ROLE.get(self.element, "Energy")

    @property
    def polarity_multiplier(self) -> float:
        return REVERSED_MULTIPLIER if self.is_reversed else UPRIGHT_MULTIPLIER

    # -- interpretation ------------------------------------------------
    @property
    def meaning(self) -> str:
        return self.reversed_meaning if self.is_reversed else self.upright_meaning

    @property
    def sports_meaning(self) -> str:
        return self.sports_reversed if self.is_reversed else self.sports_upright

    @property
    def suit_profile(self) -> Optional[Dict[str, Any]]:
        if self.suit is None:
            return None
        return SUIT_PROFILE.get(self.suit)

    def score(self, synergy_bonus: float = 0.0) -> float:
        """``(base_power x polarity) + elemental synergy bonus``."""
        return (self.base_power * self.polarity_multiplier) + synergy_bonus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "orientation": self.orientation,
            "position": self.position,
            "element": self.element,
            "role": self.role,
            "suit": self.suit,
            "arcana": self.arcana,
            "base_power": self.base_power,
            "polarity_multiplier": self.polarity_multiplier,
            "score": round(self.score(), 2),
            "meaning": self.meaning,
            "sports_meaning": self.sports_meaning,
        }


@dataclass
class EnergyProfile:
    """Scored output for one 3-card spread."""

    cards: List[Card]
    attack: float = 0.0
    defence: float = 0.0
    midfield: float = 0.0
    strategy: float = 0.0
    synergy_bonus: float = 0.0
    suit_counts: Dict[str, int] = field(default_factory=dict)
    dominant_suit: Optional[str] = None
    suit_narrative: str = ""
    dominant_element: Optional[str] = None

    @property
    def total_power(self) -> float:
        return sum(card.score(self.synergy_bonus) for card in self.cards)

    @property
    def attack_strength(self) -> float:
        """Attack rating normalised to a 0-100 scale."""
        return _normalise(self.attack / ELEMENT_SCALE * 100.0)

    @property
    def defence_strength(self) -> float:
        """Defence rating normalised to a 0-100 scale."""
        return _normalise(self.defence / ELEMENT_SCALE * 100.0)

    @property
    def midfield_strength(self) -> float:
        """Midfield/flow rating normalised to a 0-100 scale."""
        return _normalise(self.midfield / ELEMENT_SCALE * 100.0)

    @property
    def strategy_strength(self) -> float:
        """Tactical rating normalised to a 0-100 scale."""
        return _normalise(self.strategy / ELEMENT_SCALE * 100.0)

    @property
    def momentum(self) -> float:
        """Attack vs defence balance: >0 favours the attack."""
        return self.attack - self.defence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cards": [card.to_dict() for card in self.cards],
            "attack": round(self.attack, 2),
            "defence": round(self.defence, 2),
            "midfield": round(self.midfield, 2),
            "strategy": round(self.strategy, 2),
            "attack_strength": self.attack_strength,
            "defence_strength": self.defence_strength,
            "midfield_strength": self.midfield_strength,
            "strategy_strength": self.strategy_strength,
            "total_power": round(self.total_power, 2),
            "momentum": round(self.momentum, 2),
            "synergy_bonus": round(self.synergy_bonus, 2),
            "suit_counts": self.suit_counts,
            "dominant_suit": self.dominant_suit,
            "suit_narrative": self.suit_narrative,
            "dominant_element": self.dominant_element,
        }


def _normalise(value: float) -> float:
    """Clamp to a 0-100 range."""
    return max(0.0, min(100.0, value))


def load_deck(deck_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load and validate the deck configuration file."""
    path = Path(deck_path) if deck_path else DECK_PATH
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    if "major_arcana" not in data or "minor_arcana" not in data:
        raise ValueError(f"Deck file {path} is missing major/minor arcana keys")

    total = len(data["major_arcana"]) + sum(
        len(cards) for cards in data["minor_arcana"].values()
    )
    if total != 78:
        raise ValueError(f"Expected a 78-card deck, found {total}")
    return data


class TarotEngine:
    """Draws, scores and narrates tarot spreads."""

    def __init__(
        self,
        deck_path: Optional[Path] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        self._data = load_deck(deck_path)
        self.rng = rng or random.Random()
        self._flat: List[Dict[str, Any]] = []
        for card in self._data["major_arcana"]:
            self._flat.append(card)
        for suit_cards in self._data["minor_arcana"].values():
            self._flat.extend(suit_cards)

    # ------------------------------------------------------------------
    # Deck access
    # ------------------------------------------------------------------
    @property
    def cards(self) -> List[Dict[str, Any]]:
        return self._flat

    @property
    def deck_size(self) -> int:
        return len(self._flat)

    def find_card(self, name: str) -> Dict[str, Any]:
        """Look a card up by (case-insensitive) name."""
        target = name.strip().lower()
        for card in self._flat:
            if card["name"].lower() == target:
                return card
        raise KeyError(f"{name!r} is not in the deck")

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw_card(self, reversal_chance: float = 0.35) -> Card:
        """Draw a single random card."""
        return self.draw(1, reversal_chance=reversal_chance)[0]

    def draw(
        self,
        count: int,
        reversal_chance: float = 0.35,
        positions: Sequence[str] = SPREAD_POSITIONS,
    ) -> List[Card]:
        """Draw ``count`` distinct cards, assigning spread positions.

        ``reversal_chance`` is the probability a card lands reversed; real
        tarot uses roughly a third of the deck reversed, which is the default.
        """
        if not 0.0 <= reversal_chance <= 1.0:
            raise ValueError("reversal_chance must be between 0.0 and 1.0")
        if count > self.deck_size:
            raise ValueError(
                f"Cannot draw {count} cards from a {self.deck_size} card deck"
            )

        chosen = self.rng.sample(self._flat, count)
        cards: List[Card] = []
        for index, raw in enumerate(chosen):
            cards.append(
                Card(
                    name=raw["name"],
                    element=raw["element"],
                    base_power=raw["base_power"],
                    arcana=raw["arcana"],
                    suit=raw.get("suit"),
                    rank=raw.get("rank", raw["name"]),
                    is_reversed=self.rng.random() < reversal_chance,
                    upright_meaning=raw["upright_meaning"],
                    reversed_meaning=raw["reversed_meaning"],
                    sports_upright=raw["sports_upright"],
                    sports_reversed=raw["sports_reversed"],
                    position=positions[index] if index < len(positions) else None,
                )
            )
        return cards

    def draw_team_spread(self, reversal_chance: float = 0.35) -> List[Card]:
        """Draw the 3-card team spread: Attack / Defence / Key Energy."""
        return self.draw(3, reversal_chance=reversal_chance)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    @staticmethod
    def elemental_synergy_bonus(cards: Sequence[Card]) -> float:
        """Bonus awarded for a spread that plays to one element or one suit.

        Two or more cards in the same elemental current read as coherent
        game-model energy; three locked in one suit is a specialist side and
        gets the full bonus.
        """
        if not cards:
            return 0.0

        element_counts: Dict[str, int] = {}
        suit_counts: Dict[str, int] = {}
        majors = 0
        for card in cards:
            element_counts[card.element] = element_counts.get(card.element, 0) + 1
            if card.suit:
                suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
            if card.arcana == "major":
                majors += 1

        best_element = max(element_counts.values())
        best_suit = max(suit_counts.values()) if suit_counts else 0

        bonus = 0.0
        if best_element >= 3:
            bonus += 5.0
        elif best_element == 2:
            bonus += 2.5
        if best_suit >= 3:
            bonus += 5.0
        elif best_suit == 2:
            bonus += 2.5
        if majors >= 2:
            bonus += MAJOR_EVENT_BONUS / 2.0
        elif majors == 1:
            bonus += MAJOR_EVENT_BONUS / 3.0
        return bonus

    @staticmethod
    def score_spread(cards: Sequence[Card]) -> EnergyProfile:
        """Turn a drawn spread into attack/defence/midfield/strategy ratings."""
        if not cards:
            raise ValueError("Cannot score an empty spread")

        synergy = TarotEngine.elemental_synergy_bonus(cards)
        element_totals: Dict[str, float] = {
            "Fire": 0.0,
            "Water": 0.0,
            "Earth": 0.0,
            "Air": 0.0,
        }
        suit_counts: Dict[str, int] = {}

        for card in cards:
            value = card.score(synergy)
            element_totals[card.element] = element_totals.get(card.element, 0.0) + value
            if card.suit:
                suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1

        dominant_suit = None
        suit_narrative = "A Major-Arcana-heavy spread with no suit bias."
        if suit_counts:
            dominant_suit = max(suit_counts, key=lambda key: suit_counts[key])
            profile = SUIT_PROFILE[dominant_suit]
            suit_narrative = f"{profile['label']}: {profile['tempo']}."

        dominant_element = max(element_totals, key=lambda key: element_totals[key])

        return EnergyProfile(
            cards=list(cards),
            attack=element_totals["Fire"],
            defence=element_totals["Earth"],
            midfield=element_totals["Water"],
            strategy=element_totals["Air"],
            synergy_bonus=synergy,
            suit_counts=suit_counts,
            dominant_suit=dominant_suit,
            suit_narrative=suit_narrative,
            dominant_element=dominant_element,
        )

    # ------------------------------------------------------------------
    # Reversed view (for the match-day card)
    # ------------------------------------------------------------------
    def match_context(self, reversal_chance: float = 0.5) -> Card:
        """Draw the single 'match context' card describing the fixture itself."""
        raw = self.rng.choice(self._flat)
        return Card(
            name=raw["name"],
            element=raw["element"],
            base_power=raw["base_power"],
            arcana=raw["arcana"],
            suit=raw.get("suit"),
            rank=raw.get("rank", raw["name"]),
            is_reversed=self.rng.random() < reversal_chance,
            upright_meaning=raw["upright_meaning"],
            reversed_meaning=raw["reversed_meaning"],
            sports_upright=raw["sports_upright"],
            sports_reversed=raw["sports_reversed"],
            position="Match Context",
        )


# ----------------------------------------------------------------------
# Interpretation
# ----------------------------------------------------------------------
_POSITION_LENS: Dict[str, str] = {
    "Attack": (
        "reads as the engine room of this attack - the quality of the shots "
        "this team will actually take"
    ),
    "Defence": (
        "describes the defensive line: what is happening in front of the "
        "keeper when the opposition comes at it"
    ),
    "Key Energy": (
        "is the emotional weather of the whole performance - the thing that "
        "will make this match feel the way it does"
    ),
    "Match Context": (
        "sets the tone of the fixture itself, above both teams' individual "
        "readings"
    ),
}


def explain_card(card: Card) -> str:
    """One-card narrative explaining why the card was drawn."""
    orientation_clause = (
        f"{card.name} comes to you reversed"
        if card.is_reversed
        else f"{card.name} falls upright"
    )
    parts = [
        f"**{card.display_name}** ({card.position or 'Card'}) - {orientation_clause}.",
        f"*General reading:* {card.meaning}.",
        f"*On the pitch:* {card.sports_meaning}.",
    ]
    lens = _POSITION_LENS.get(card.position or "")
    if lens:
        parts.append(f"*Why here:* In the {card.position} slot it {lens}.")
    parts.append(
        f"*Numerically:* base power {card.base_power}/100 x "
        f"{card.polarity_multiplier} ({card.orientation.lower()} polarity) = "
        f"{card.score():.1f} effective power."
    )
    profile = card.suit_profile
    if profile:
        parts.append(f"*Tempo signal:* {profile['tempo']}.")
    return " ".join(parts)


def explain_draw(
    cards_drawn: Sequence[Card],
    team_name: str,
    profile: Optional[EnergyProfile] = None,
) -> str:
    """Narrate a team's 3-card spread card by card, then as one story.

    This is the dedicated explanation generator required by the spec.
    """
    if not cards_drawn:
        return f"No cards were drawn for {team_name}, so the spread has nothing to say."

    profile = profile or score_cards(cards_drawn)

    lines: List[str] = [f"=== CARD EXPLANATION: {team_name} ===", ""]

    for card in cards_drawn:
        lines.append(explain_card(card))
        lines.append("")

    # ---- Synergy story ----------------------------------------------
    lines.append(f"--- SYNERGY STORY: {team_name} ---")
    lines.append("")

    upright_count = sum(1 for card in cards_drawn if not card.is_reversed)
    reversed_count = len(cards_drawn) - upright_count

    if upright_count == len(cards_drawn):
        lines.append(
            "All three cards land upright. Nothing is being fought against: the "
            "whole side turns up to play the game it has trained for."
        )
    elif reversed_count == len(cards_drawn):
        lines.append(
            "All three cards are reversed. This is a team fighting its own "
            "instincts - the talent is obvious, but the expression is stuck in "
            "the wrong gear."
        )
    else:
        lines.append(
            f"{upright_count} upright against {reversed_count} reversed: a side "
            "with one foot on the accelerator and one dragging in the dirt."
        )

    lines.append("")
    lines.append(profile.suit_narrative)

    attack = profile.attack_strength
    defence = profile.defence_strength

    # A three-card spread often contains no card for a given element. A zero
    # strength then means "nothing was drawn for that role", not "this team is
    # hopeless at it", so the balance narrative has to distinguish the two.
    drawn_elements = {card.element for card in cards_drawn}
    has_fire = "Fire" in drawn_elements
    has_earth = "Earth" in drawn_elements

    if has_fire and not has_earth:
        lines.append(
            f"No Earth card was drawn, so there is no defensive reading here at "
            f"all; the spread simply says nothing about how this team defends. "
            f"What it does show is {attack:.0f} attack strength - the cards "
            "point to a side that will be busy going forward."
        )
    elif has_earth and not has_fire:
        lines.append(
            f"No Fire card was drawn, so this spread makes no claim about "
            f"attacking threat. It does show {defence:.0f} defence strength: "
            "the cards describe a side that would rather not be exposed."
        )
    elif attack - defence > 18:
        lines.append(
            f"The spread is front-loaded: attack {attack:.0f} against defence "
            f"{defence:.0f}. This team wants the game to stay open and will "
            "push men forward for the full ninety."
        )
    elif defence - attack > 18:
        lines.append(
            f"The spread is back-loaded: defence {defence:.0f} against attack "
            f"{attack:.0f}. This team wants the game to stay tight and will "
            "look for one moment to hurt the opposition."
        )
    else:
        lines.append(
            f"A genuinely balanced spread - attack {attack:.0f}, defence "
            f"{defence:.0f}. This side can win whichever half of the pitch "
            "the match turns on."
        )

    majors = [card for card in cards_drawn if card.arcana == "major"]
    if len(majors) >= 2:
        lines.append(
            f"{len(majors)} of {len(cards_drawn)} cards are Major Arcana: this "
            "fixture is fated to be decided by an event - an own goal, a "
            "red card, a freak finish, a moment that rewrites the match."
        )

    lines.append("")
    lines.append(
        f"*Total spread power:* {profile.total_power:.1f} "
        f"(attack {profile.attack:.1f} / defence {profile.defence:.1f} / "
        f"midfield {profile.midfield:.1f} / strategy {profile.strategy:.1f}, "
        f"synergy bonus {profile.synergy_bonus:.1f})."
    )
    return "\n".join(lines)


def score_cards(cards: Sequence[Card]) -> EnergyProfile:
    """Score an arbitrary spread without constructing an engine instance."""
    return TarotEngine.score_spread(cards)


def format_card_line(card: Card) -> str:
    """Compact one-line rendering used in the comparison matrix."""
    return (
        f"{card.display_name} - {card.role} "
        f"[{card.element}] power {card.score():.0f}"
    )