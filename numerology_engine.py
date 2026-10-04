"""Numerology engine: Pythagorean / Chaldean letter maps, date reduction,
expression numbers and match-day compatibility scoring."""

from __future__ import annotations

import re
from datetime import date
from typing import Dict, List, Optional

# --------------------------------------------------------------------------
# Letter -> number mappings
# --------------------------------------------------------------------------

PYTHAGOREAN_MAP: Dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 6, "P": 7, "Q": 8, "R": 9,
    "S": 1, "T": 2, "U": 3, "V": 4, "W": 5, "X": 6, "Y": 7, "Z": 8,
}

CHALDEAN_MAP: Dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 8, "G": 3, "H": 5, "I": 1,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 7, "P": 8, "Q": 1, "R": 2,
    "S": 3, "T": 4, "U": 6, "V": 6, "W": 6, "X": 5, "Y": 1, "Z": 7,
}

MASTER_NUMBERS = (11, 22, 33)

NUMBER_MEANINGS: Dict[int, str] = {
    1: "Leadership and the initiator. A day for first moves and individual "
       "brilliance - expect one side to carry the individual burden.",
    2: "Partnership and duality. The day rewards balance, assists and "
       "two-way play; solo improvisation tends to falter.",
    3: "Expression and expansion. Creative, free-flowing energy favours "
       "attacking football, flair and a high-event game.",
    4: "Structure and discipline. Order, shape and set-piece organisation "
       "dominate; sloppy transitional moments are punished.",
    5: "Change and volatility. An unpredictable, end-to-end fixture where "
       "momentum swings matter more than settled control.",
    6: "Harmony and balance. A measured, tactical day; well-drilled sides "
       "thrive while impatient ones concede cheap chances.",
    7: "Introspection and analysis. A cerebral, low-tempo day - pressing "
       "triggers and studied set plays over frantic football.",
    8: "Power and material reward. Financial/ambition energy maps well onto "
       "teams chasing prize money; intensity is high.",
    9: "Completion and drama. Endings, late goals and emotional weight; the "
       "final third of matches tends to decide the result.",
    11: "MASTER NUMBER - Intuition and illumination. A highly sensitive "
         "day: inspiration flows, but nerves are equally exposed.",
    22: "MASTER NUMBER - The Master Builder. Monumental structural energy; "
         "large frameworks and decisive moves define the fixture.",
    33: "MASTER NUMBER - The healer/teacher. Rare, compassionate energy that "
         "favours emotional resilience and collective lift.",
}


class NumerologyEngine:
    """Pure, deterministic numerology helpers (no randomness)."""

    # ------------------------------------------------------------------
    # Core reduction
    # ------------------------------------------------------------------
    @staticmethod
    def reduce_number(number: int) -> int:
        """Digit-sum reduction that preserves Master Numbers (11/22/33)."""
        if number < 0:
            raise ValueError("reduce_number requires a non-negative integer")
        while number > 9:
            if number in MASTER_NUMBERS:
                return number
            number = sum(int(digit) for digit in str(number))
        return number

    @staticmethod
    def digit_sum(number: int) -> int:
        """Single-pass digit sum (used for the intermediate reduction step)."""
        return sum(int(digit) for digit in str(number))

    # ------------------------------------------------------------------
    # Date energy
    # ------------------------------------------------------------------
    @staticmethod
    def parse_date(date_str: str) -> date:
        """Parse ``YYYY-MM-DD`` (the canonical CLI/UI format)."""
        try:
            return date.fromisoformat(date_str.strip())
        except ValueError as exc:  # pragma: no cover - trivial re-raise
            raise ValueError(
                f"Invalid date {date_str!r}; expected YYYY-MM-DD"
            ) from exc

    def date_digits(self, match_date: str) -> List[int]:
        """Every digit of the match date, in order (year, month, day)."""
        parsed = self.parse_date(match_date)
        digits: List[int] = []
        for chunk in (parsed.year, parsed.month, parsed.day):
            digits.extend(int(d) for d in str(chunk))
        return digits

    def match_day_life_path(self, match_date: str) -> int:
        """Life Path of the match date, Master Numbers preserved.

        Uses the classic Pythagorean date reduction: reduce the day and the
        month individually, then add them to the reduced year and reduce the
        total once more.
        """
        parsed = self.parse_date(match_date)
        day = self.reduce_number(parsed.day)
        month = self.reduce_number(parsed.month)
        year = self.reduce_number(self.digit_sum(parsed.year))
        return self.reduce_number(day + month + year)

    # ------------------------------------------------------------------
    # Name energy
    # ------------------------------------------------------------------
    @staticmethod
    def normalise_name(name: str) -> str:
        """Upper-case the name and strip every non-alphabetic character."""
        return re.sub(r"[^A-Za-z]", "", name.upper())

    def name_total(self, name: str, system: str = "pythagorean") -> int:
        """Un-reduced letter sum for a team/expression name."""
        mapping = self._mapping(system)
        return sum(
            mapping[char]
            for char in self.normalise_name(name)
            if char in mapping
        )

    def expression_number(self, name: str, system: str = "pythagorean") -> int:
        """Reduced Expression (Destination) number for a name."""
        return self.reduce_number(self.name_total(name, system))

    def name_to_number(self, name: str, system: str = "pythagorean") -> int:
        """Reduced letter sum for a name (alias of :meth:`expression_number`)."""
        return self.expression_number(name, system)

    @staticmethod
    def _mapping(system: str) -> Dict[str, int]:
        key = system.strip().lower()
        if key == "pythagorean":
            return PYTHAGOREAN_MAP
        if key == "chaldean":
            return CHALDEAN_MAP
        raise ValueError(
            f"Unknown numerology system {system!r}; "
            "expected 'pythagorean' or 'chaldean'"
        )

    # ------------------------------------------------------------------
    # Compatibility
    # ------------------------------------------------------------------
    @staticmethod
    def number_meaning(value: int) -> str:
        """Narrative description for a Life Path / Expression number."""
        return NUMBER_MEANINGS.get(value, "A numerically unremarkable day.")

    @staticmethod
    def _wheel_position(value: int) -> int:
        """Map any number onto the 1-9 wheel.

        Master numbers fold back onto their base vibration so that 11, 22
        and 33 can be compared against ordinary single digits.
        """
        position = value % 9
        return 9 if position == 0 else position

    @classmethod
    def compatibility(cls, team_number: int, day_number: int) -> float:
        """Day-of-game luck score (0-100) between a team number and the date.

        The comparison is circular: 1 and 9 sit next to each other on the
        wheel, while 1 and 5 sit directly opposite and score near zero. A
        Master Number day adds a resonance bonus on top.
        """
        if team_number <= 0 or day_number <= 0:
            return 0.0

        team_position = cls._wheel_position(team_number)
        day_position = cls._wheel_position(day_number)

        raw_distance = abs(team_position - day_position)
        wheel_distance = min(raw_distance, 9 - raw_distance)
        proximity = 1.0 - (wheel_distance / 4.0)

        score = proximity * 100.0
        if day_number in MASTER_NUMBERS:
            score += 8.0
        if team_number in MASTER_NUMBERS:
            score += 4.0
        return round(max(0.0, min(100.0, score)), 1)

    @staticmethod
    def head_to_head(team_a: int, team_b: int) -> float:
        """Mirror-harmony score between the two teams' numbers (0-100)."""
        return NumerologyEngine.compatibility(team_a, team_b)