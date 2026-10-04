"""Predictor: fuses the tarot spread scores with numerology into goal ranges,
win/draw probabilities and a final consensus verdict."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from numerology_engine import NumerologyEngine
from tarot_engine import (
    SUIT_PROFILE,
    Card,
    EnergyProfile,
    TarotEngine,
    explain_draw,
    format_card_line,
)

#: Baseline goals for an average, neutral fixture before card energy is applied.
BASE_GOALS = 1.35

#: How much a team's card attack/defence swings its scoring expectation.
ATTACK_WEIGHT = 1.10
DEFENCE_OPPOSITION_WEIGHT = 0.85

#: Multiplier applied when the spread has no Fire card at all (dry attack).
COLD_ATTACK_PENALTY = 0.70

#: Numerology contributes at most this many goals either way.
NUMEROLOGY_GOAL_SWING = 0.55
NUMEROLOGY_GOAL_LEAN = NUMEROLOGY_GOAL_SWING

#: Verdict thresholds on the combined confidence score (0-100).
WIN_THRESHOLD = 54.0
DRAW_THRESHOLD = 46.0


@dataclass
class TeamReading:
    """Everything the two engines say about one team."""

    name: str
    cards: List[Card]
    profile: EnergyProfile
    expression_number: int
    expression_total: int
    chaldean_number: int
    compatibility: float
    day_vibe: str
    explanation: str
    expected_goals: float = 0.0
    goal_range: Tuple[int, int] = (0, 0)
    primary_goals: int = 0
    goal_basis: str = ""
    score: float = 0.0
    probability: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cards": [card.to_dict() for card in self.cards],
            "card_lines": [format_card_line(card) for card in self.cards],
            "profile": self.profile.to_dict(),
            "expression_number": self.expression_number,
            "expression_total": self.expression_total,
            "chaldean_number": self.chaldean_number,
            "compatibility": self.compatibility,
            "day_vibe": self.day_vibe,
            "explanation": self.explanation,
            "expected_goals": round(self.expected_goals, 2),
            "goal_range": list(self.goal_range),
            "primary_goals": self.primary_goals,
            "goal_basis": self.goal_basis,
            "score": round(self.score, 2),
            "probability": round(self.probability, 1),
        }


@dataclass
class NumerologyReading:
    """The numerology view of the fixture, kept as its own object."""

    life_path: int
    life_path_meaning: str
    team_a_expression: int
    team_b_expression: int
    team_a_chaldean: int
    team_b_chaldean: int
    team_a_compatibility: float
    team_b_compatibility: float
    harmony: float
    goal_bias: float
    narrative: str
    winner: str
    draw_probability: float
    winner_probability: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "life_path": self.life_path,
            "life_path_meaning": self.life_path_meaning,
            "team_a_expression": self.team_a_expression,
            "team_b_expression": self.team_b_expression,
            "team_a_chaldean": self.team_a_chaldean,
            "team_b_chaldean": self.team_b_chaldean,
            "team_a_compatibility": self.team_a_compatibility,
            "team_b_compatibility": self.team_b_compatibility,
            "harmony": round(self.harmony, 1),
            "goal_bias": round(self.goal_bias, 2),
            "narrative": self.narrative,
            "winner": self.winner,
            "draw_probability": round(self.draw_probability, 1),
            "winner_probability": round(self.winner_probability, 1),
        }


@dataclass
class MatchPrediction:
    """The full combined reading for one fixture."""

    team_a: str
    team_b: str
    match_date: str
    tarot: Dict[str, Any]
    numerology: NumerologyReading
    reading_a: TeamReading
    reading_b: TeamReading
    match_card: Card
    score_a: float = 0.0
    score_b: float = 0.0
    predicted_goals_a: int = 0
    predicted_goals_b: int = 0
    tarot_winner: str = ""
    numerology_winner: str = ""
    consensus_winner: str = ""
    confidence: float = 0.0
    verdict_reasoning: str = ""
    draw_probability: float = 0.0
    winner_probability: float = 0.0
    combined: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_a": self.team_a,
            "team_b": self.team_b,
            "match_date": self.match_date,
            "match_card": self.match_card.to_dict(),
            "tarot": self.tarot,
            "numerology": self.numerology.to_dict(),
            "team_a_reading": self.reading_a.to_dict(),
            "team_b_reading": self.reading_b.to_dict(),
            "score_a": round(self.score_a, 1),
            "score_b": round(self.score_b, 1),
            "predicted_goals": {
                "team_a": self.predicted_goals_a,
                "team_b": self.predicted_goals_b,
            },
            "tarot_winner": self.tarot_winner,
            "numerology_winner": self.numerology_winner,
            "consensus_winner": self.consensus_winner,
            "confidence": round(self.confidence, 1),
            "verdict_reasoning": self.verdict_reasoning,
            "draw_probability": round(self.draw_probability, 1),
            "winner_probability": round(self.winner_probability, 1),
        }


class Predictor:
    """Combines :class:`TarotEngine` and :class:`NumerologyEngine`."""

    def __init__(
        self,
        tarot: Optional[TarotEngine] = None,
        numerology: Optional[NumerologyEngine] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.rng = rng or random.Random()
        self.tarot = tarot or TarotEngine(rng=self.rng)
        self.numerology = numerology or NumerologyEngine()

    # ------------------------------------------------------------------
    # Numerology side
    # ------------------------------------------------------------------
    def analyse_numerology(
        self, team_a: str, team_b: str, match_date: str
    ) -> NumerologyReading:
        life_path = self.numerology.match_day_life_path(match_date)
        expr_a = self.numerology.expression_number(team_a)
        expr_b = self.numerology.expression_number(team_b)
        chal_a = self.numerology.expression_number(team_a, "chaldean")
        chal_b = self.numerology.expression_number(team_b, "chaldean")

        compat_a = self.numerology.compatibility(expr_a, life_path)
        compat_b = self.numerology.compatibility(expr_b, life_path)
        harmony = self.numerology.head_to_head(expr_a, expr_b)

        edge = compat_a - compat_b
        goal_bias = max(
            -NUMEROLOGY_GOAL_LEAN, min(NUMEROLOGY_GOAL_LEAN, edge / 100.0 * 2.0)
        )

        narrative = self._numerology_narrative(
            team_a, team_b, life_path, expr_a, expr_b, compat_a, compat_b, harmony
        )

        winner, draw_probability, winner_probability = self._numerology_verdict(
            team_a, team_b, life_path, compat_a, compat_b, harmony
        )

        return NumerologyReading(
            life_path=life_path,
            life_path_meaning=self.numerology.number_meaning(life_path),
            team_a_expression=expr_a,
            team_b_expression=expr_b,
            team_a_chaldean=chal_a,
            team_b_chaldean=chal_b,
            team_a_compatibility=compat_a,
            team_b_compatibility=compat_b,
            harmony=harmony,
            goal_bias=goal_bias,
            narrative=narrative,
            winner=winner,
            draw_probability=draw_probability,
            winner_probability=winner_probability,
        )

    def _numerology_narrative(
        self,
        team_a: str,
        team_b: str,
        life_path: int,
        expr_a: int,
        expr_b: int,
        compat_a: float,
        compat_b: float,
        harmony: float,
    ) -> str:
        parts = [
            f"The match date carries a Life Path of {life_path}. "
            f"{self.numerology.number_meaning(life_path)}",
            f"{team_a} reduces to Expression {expr_a} "
            f"(Pythagorean) and {self.numerology.expression_number(team_a, 'chaldean')} "
            f"(Chaldean); {team_b} reduces to Expression {expr_b} "
            f"(Pythagorean) and {self.numerology.expression_number(team_b, 'chaldean')} "
            f"(Chaldean).",
            f"Against the date, {team_a} scores {compat_a:.0f}/100 for "
            f"day-of-game luck and {team_b} scores {compat_b:.0f}/100.",
        ]
        gap = abs(compat_a - compat_b)
        if gap < 4:
            parts.append(
                "The two names sit almost in phase with each other: the "
                "fixture is numerically level and the cards will have to break it."
            )
        else:
            favoured = team_a if compat_a > compat_b else team_b
            parts.append(
                f"{favoured} is the name the date happens to favour, by "
                f"{gap:.0f} points of compatibility."
            )
        if harmony >= 75:
            parts.append(
                "The mirror-harmony between the two names is very high, which "
                "usually reads as a cagey, respectful fixture."
            )
        elif harmony <= 30:
            parts.append(
                "The names barely resonate with each other: expect friction, "
                "cards, and a match decided by temperament rather than plan."
            )
        return " ".join(parts)

    def _numerology_verdict(
        self,
        team_a: str,
        team_b: str,
        life_path: int,
        compat_a: float,
        compat_b: float,
        harmony: float,
    ) -> Tuple[str, float, float]:
        gap = abs(compat_a - compat_b)
        leader = team_a if compat_a > compat_b else team_b

        if gap < 2.0:
            winner = "Draw"
            draw_probability = min(60.0, 38.0 + harmony / 4.0)
        else:
            winner = leader
            draw_probability = max(18.0, 34.0 - gap * 1.4)

        winner_probability = round(100.0 - draw_probability, 1)
        return winner, round(draw_probability, 1), winner_probability

    # ------------------------------------------------------------------
    # Tarot goal model
    # ------------------------------------------------------------------
    def goal_expectation(
        self,
        profile: EnergyProfile,
        opponent: EnergyProfile,
        numerology_bias: float = 0.0,
    ) -> Tuple[float, str]:
        """Expected goals for a team, plus a human-readable derivation."""
        attack_component = (profile.attack_strength / 100.0) * ATTACK_WEIGHT
        concession_component = (
            (opponent.defence_strength / 100.0) * DEFENCE_OPPOSITION_WEIGHT
        )

        goals = BASE_GOALS + attack_component - concession_component
        goals += numerology_bias

        notes: List[str] = []

        if profile.attack <= 0.0:
            goals *= COLD_ATTACK_PENALTY
            notes.append(
                f"No Fire card in the spread, so the attack multiplier of "
                f"{COLD_ATTACK_PENALTY} is applied"
            )

        if profile.dominant_suit:
            profile_data = SUIT_PROFILE[profile.dominant_suit]
            suit_shift = profile_data["goal_delta"] * 0.40
            goals += suit_shift
            notes.append(
                f"{profile_data['label']} dominance shifts the line by "
                f"{suit_shift:+.2f}"
            )

        if numerology_bias:
            notes.append(
                f"numerology compatibility adjusts by {numerology_bias:+.2f}"
            )

        derivation = (
            f"base {BASE_GOALS:.2f} + attack {attack_component:+.2f} "
            f"- opponent defence {concession_component:.2f}"
            f" = {goals:.2f}"
        )
        if notes:
            derivation += "; " + "; ".join(notes)
        return max(0.15, goals), derivation

    @staticmethod
    def goal_range(expected: float, variance: float = 0.55) -> Tuple[int, int, int]:
        """Primary goal count plus a realistic low/high band."""
        primary = int(round(expected))
        low = max(0, int(round(expected - variance)))
        high = primary + int(round(variance))
        return primary, low, high

    @staticmethod
    def _finalise_range(primary: int, is_winner: bool) -> Tuple[int, int]:
        """A tight, believable band around the predicted primary count."""
        if primary <= 0:
            return (0, 1)
        if primary == 1:
            return (0, 2)
        if is_winner:
            return (primary - 1, primary + 2)
        return (max(0, primary - 2), primary + 1)

    # ------------------------------------------------------------------
    # Full prediction
    # ------------------------------------------------------------------
    def predict(
        self,
        team_a: str,
        team_b: str,
        match_date: Optional[str] = None,
    ) -> MatchPrediction:
        if not team_a.strip() or not team_b.strip():
            raise ValueError("Both team names are required")
        if match_date is None:
            match_date = date.today().isoformat()
        # Validate the date up front so bad input fails loudly.
        NumerologyEngine.parse_date(match_date)

        numerology = self.analyse_numerology(team_a, team_b, match_date)

        cards_a = self.tarot.draw_team_spread()
        cards_b = self.tarot.draw_team_spread()
        profile_a = self.tarot.score_spread(cards_a)
        profile_b = self.tarot.score_spread(cards_b)
        match_card = self.tarot.match_context()

        goals_a, basis_a = self.goal_expectation(
            profile_a, profile_b, numerology.goal_bias
        )
        goals_b, basis_b = self.goal_expectation(
            profile_b, profile_a, -numerology.goal_bias
        )

        primary_a, _, _ = self.goal_range(goals_a)
        primary_b, _, _ = self.goal_range(goals_b)

        score_a = self._team_score(
            profile_a, profile_b, numerology.team_a_compatibility, goals_a
        )
        score_b = self._team_score(
            profile_b, profile_a, numerology.team_b_compatibility, goals_b
        )

        reading_a = TeamReading(
            name=team_a,
            cards=cards_a,
            profile=profile_a,
            expression_number=numerology.team_a_expression,
            expression_total=self.numerology.name_total(team_a),
            chaldean_number=numerology.team_a_chaldean,
            compatibility=numerology.team_a_compatibility,
            day_vibe=numerology.life_path_meaning,
            explanation=explain_draw(cards_a, team_a, profile_a),
            expected_goals=goals_a,
            goal_range=self._finalise_range(primary_a, False),
            primary_goals=primary_a,
            goal_basis=basis_a,
            score=score_a,
        )
        reading_b = TeamReading(
            name=team_b,
            cards=cards_b,
            profile=profile_b,
            expression_number=numerology.team_b_expression,
            expression_total=self.numerology.name_total(team_b),
            chaldean_number=numerology.team_b_chaldean,
            compatibility=numerology.team_b_compatibility,
            day_vibe=numerology.life_path_meaning,
            explanation=explain_draw(cards_b, team_b, profile_b),
            expected_goals=goals_b,
            goal_range=self._finalise_range(primary_b, False),
            primary_goals=primary_b,
            goal_basis=basis_b,
            score=score_b,
        )

        tarot_winner = self._decide_winner(team_a, team_b, score_a, score_b)
        consensus = self._consensus(
            team_a,
            team_b,
            score_a,
            score_b,
            tarot_winner,
            numerology.winner,
            match_card,
        )
        confidence = abs(score_a - score_b)
        gap = abs(goals_a - goals_b)
        draw_probability = max(12.0, 46.0 - gap * 22.0 - confidence * 0.25)
        winner_probability = 100.0 - draw_probability

        primary_a, primary_b = self._apply_winner_lean(
            primary_a, primary_b, consensus, team_a, team_b
        )
        reading_a.primary_goals = primary_a
        reading_b.primary_goals = primary_b
        reading_a.goal_range = self._finalise_range(primary_a, consensus == team_a)
        reading_b.goal_range = self._finalise_range(primary_b, consensus == team_b)
        reading_a.probability = winner_probability if consensus == team_a else draw_probability
        reading_b.probability = winner_probability if consensus == team_b else draw_probability

        return MatchPrediction(
            team_a=team_a,
            team_b=team_b,
            match_date=match_date,
            tarot={
                "team_a": reading_a.to_dict(),
                "team_b": reading_b.to_dict(),
                "match_card": match_card.to_dict(),
            },
            numerology=numerology,
            reading_a=reading_a,
            reading_b=reading_b,
            match_card=match_card,
            score_a=score_a,
            score_b=score_b,
            predicted_goals_a=primary_a,
            predicted_goals_b=primary_b,
            tarot_winner=tarot_winner,
            numerology_winner=numerology.winner,
            consensus_winner=consensus,
            confidence=confidence,
            verdict_reasoning=self._verdict_reasoning(
                team_a, team_b, score_a, score_b, consensus, match_card
            ),
            draw_probability=draw_probability,
            winner_probability=winner_probability,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _team_score(
        profile: EnergyProfile,
        opponent: EnergyProfile,
        compatibility: float,
        expected_goals: float,
    ) -> float:
        """Blend card energy and numerology into a single 0-100 team score."""
        attack = profile.attack_strength
        defence = profile.defence_strength
        midfield = profile.midfield_strength
        strategy = profile.strategy_strength

        card_component = (
            attack * 0.34 + defence * 0.26 + midfield * 0.22 + strategy * 0.18
        )
        opposition_penalty = opponent.attack_strength * 0.22
        numerology_component = compatibility * 0.30
        goal_component = min(100.0, expected_goals * 30.0) * 0.25

        raw = (
            card_component
            - opposition_penalty
            + numerology_component
            + goal_component
        )
        return max(0.0, min(100.0, raw))

    @staticmethod
    def _decide_winner(
        team_a: str, team_b: str, score_a: float, score_b: float
    ) -> str:
        if abs(score_a - score_b) < 3.0:
            return "Draw"
        return team_a if score_a > score_b else team_b

    @staticmethod
    def _consensus(
        team_a: str,
        team_b: str,
        score_a: float,
        score_b: float,
        tarot_winner: str,
        numerology_winner: str,
        match_card: Card,
    ) -> str:
        """Reconcile the two systems with the match-context card."""
        card_lean = "Draw"
        if match_card.element == "Fire" and not match_card.is_reversed:
            card_lean = "attack"
        elif match_card.element == "Earth" and not match_card.is_reversed:
            card_lean = "defence"
        elif match_card.is_reversed:
            card_lean = "Draw"

        if tarot_winner == numerology_winner:
            return tarot_winner

        # The two systems disagree: break the tie with the overall card score.
        if abs(score_a - score_b) < 3.0:
            return "Draw"
        leader = team_a if score_a > score_b else team_b
        if card_lean == "Draw":
            return "Draw"
        return leader

    @staticmethod
    def _apply_winner_lean(
        primary_a: int,
        primary_b: int,
        consensus: str,
        team_a: str,
        team_b: str,
    ) -> Tuple[int, int]:
        """Nudge the scoreline so it agrees with the consensus verdict."""
        if consensus == "Draw":
            if primary_a < primary_b:
                primary_a = primary_b
            elif primary_b < primary_a:
                primary_b = primary_a
            return primary_a, primary_b
        if consensus == team_a and primary_a <= primary_b:
            primary_a = primary_b + 1
        if consensus == team_b and primary_b <= primary_a:
            primary_b = primary_a + 1
        return primary_a, primary_b

    @staticmethod
    def _verdict_reasoning(
        team_a: str,
        team_b: str,
        score_a: float,
        score_b: float,
        consensus: str,
        match_card: Card,
    ) -> str:
        margin = abs(score_a - score_b)
        if consensus == "Draw":
            lead = (
                "neither side holds a decisive edge"
                if margin < 3
                else f"the margins are too close to call ({margin:.1f} points apart)"
            )
            return (
                f"Final consensus: DRAW. The two systems could not separate "
                f"{team_a} and {team_b} - {lead}, and the match card "
                f"{match_card.display_name} refuses to tip the fixture either way."
            )
        winner_score = max(score_a, score_b)
        loser_score = min(score_a, score_b)
        return (
            f"Final consensus: {consensus.upper()}. The cards put them "
            f"{winner_score:.1f} to {loser_score:.1f} - a {margin:.1f} point "
            f"margin - and {match_card.display_name} sets a match-day tone that "
            f"does not overturn it."
        )