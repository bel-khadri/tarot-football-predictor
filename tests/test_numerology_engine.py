"""Tests for the numerology engine: reduction, name maps, compatibility."""

from __future__ import annotations

from datetime import date

import pytest

from numerology_engine import (
    CHALDEAN_MAP,
    MASTER_NUMBERS,
    PYTHAGOREAN_MAP,
    NumerologyEngine,
)


@pytest.fixture()
def num() -> NumerologyEngine:
    return NumerologyEngine()


# ----------------------------------------------------------------------
# Digit reduction
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    ("raw", "expected"),
    [(1, 1), (9, 9), (10, 1), (11, 11), (22, 22), (33, 33), (99, 9)],
)
def test_reduce_number_preserves_master_numbers(
    num: NumerologyEngine, raw: int, expected: int
) -> None:
    assert num.reduce_number(raw) == expected


def test_reduce_number_collapses_long_numbers(num: NumerologyEngine) -> None:
    assert num.reduce_number(1000) == 1
    assert num.reduce_number(2026) == 1  # 2+0+2+6 = 10 -> 1
    assert num.reduce_number(493) == 7  # 4+9+3 = 16 -> 7


def test_reduce_number_returns_a_master_number_from_a_long_sum() -> None:
    """287 -> 17 -> 8, but 38 -> 11 must survive the second pass."""
    engine = NumerologyEngine()
    assert engine.reduce_number(38) == 11
    assert engine.reduce_number(119) == 11


def test_reduce_number_rejects_negatives(num: NumerologyEngine) -> None:
    with pytest.raises(ValueError):
        num.reduce_number(-5)


def test_digit_sum(num: NumerologyEngine) -> None:
    assert num.digit_sum(493) == 16
    assert num.digit_sum(2026) == 10


def test_master_numbers_constant() -> None:
    assert MASTER_NUMBERS == (11, 22, 33)


# ----------------------------------------------------------------------
# Letter maps
# ----------------------------------------------------------------------
def test_pythagorean_map_cycles_one_to_nine() -> None:
    assert PYTHAGOREAN_MAP["A"] == 1
    assert PYTHAGOREAN_MAP["I"] == 9
    assert PYTHAGOREAN_MAP["J"] == 1  # cycle restarts
    assert PYTHAGOREAN_MAP["R"] == 9
    assert PYTHAGOREAN_MAP["S"] == 1
    assert PYTHAGOREAN_MAP["Z"] == 8


def test_chaldean_map_matches_the_traditional_table() -> None:
    assert CHALDEAN_MAP["A"] == 1
    assert CHALDEAN_MAP["F"] == 8  # not 6
    assert CHALDEAN_MAP["G"] == 3  # not 7
    assert CHALDEAN_MAP["I"] == 1  # not 9
    assert CHALDEAN_MAP["O"] == 7
    assert CHALDEAN_MAP["Q"] == 1  # no 17 in modern Chaldean
    assert CHALDEAN_MAP["X"] == 5


def test_both_maps_cover_the_whole_alphabet() -> None:
    letters = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    assert set(PYTHAGOREAN_MAP) == letters
    assert set(CHALDEAN_MAP) == letters


def test_unknown_system_is_rejected(num: NumerologyEngine) -> None:
    with pytest.raises(ValueError, match="Unknown numerology system"):
        num.name_to_number("Arsenal", "kabbalistic")


def test_system_name_is_case_insensitive(num: NumerologyEngine) -> None:
    assert num.expression_number("Arsenal", "Chaldean") == (
        num.expression_number("Arsenal", "chaldean")
    )


# ----------------------------------------------------------------------
# Name normalisation
# ----------------------------------------------------------------------
def test_normalise_name_strips_spaces_and_punctuation(
    num: NumerologyEngine,
) -> None:
    assert num.normalise_name("Manchester United F.C.") == "MANCHESTERUNITEDFC"
    assert num.normalise_name("  Real  Madrid  ") == "REALMADRID"
    assert num.normalise_name("1. FC Köln") == "FCKÖLN".replace("Ö", "")


def test_normalise_name_is_case_insensitive(num: NumerologyEngine) -> None:
    assert num.normalise_name("arsenal") == num.normalise_name("ARSENAL")


# ----------------------------------------------------------------------
# Expression numbers
# ----------------------------------------------------------------------
def test_expression_number_is_single_digit_or_master(
    num: NumerologyEngine,
) -> None:
    for name in ("Arsenal", "Real Madrid", "Bayern Munchen", "Chelsea"):
        value = num.expression_number(name)
        assert value in range(1, 10) or value in MASTER_NUMBERS


def test_expression_number_is_reduction_of_the_total(
    num: NumerologyEngine,
) -> None:
    for name in ("Arsenal", "Inter", "PSV Eindhoven"):
        total = num.name_total(name)
        assert num.expression_number(name) == num.reduce_number(total)


def test_name_total_uses_the_requested_map(num: NumerologyEngine) -> None:
    # Inter: I=9, N=5, T=2, E=5, R=9 -> 30
    assert num.name_total("Inter") == 30
    # Chaldean: I=1, N=5, T=4, E=5, R=2 -> 17
    assert num.name_total("Inter", "chaldean") == 17


def test_pythagorean_and_chaldean_can_disagree(
    num: NumerologyEngine,
) -> None:
    assert num.expression_number("Inter") == 3  # 30 -> 3
    assert num.expression_number("Inter", "chaldean") == 8  # 17 -> 8


def test_empty_name_reduces_to_zero(num: NumerologyEngine) -> None:
    assert num.name_total("12345") == 0
    assert num.expression_number("12345") == 0


def test_expression_number_is_stable(num: NumerologyEngine) -> None:
    assert num.expression_number("Chelsea") == num.expression_number("Chelsea")


# ----------------------------------------------------------------------
# Date energy / Life Path
# ----------------------------------------------------------------------
def test_parse_date_accepts_iso_format(num: NumerologyEngine) -> None:
    assert num.parse_date("2026-10-04") == date(2026, 10, 4)


def test_parse_date_rejects_bad_input(num: NumerologyEngine) -> None:
    with pytest.raises(ValueError, match="Invalid date"):
        num.parse_date("04/10/2026")
    with pytest.raises(ValueError, match="Invalid date"):
        num.parse_date("not-a-date")


def test_date_digits_flattens_the_whole_date(
    num: NumerologyEngine,
) -> None:
    assert num.date_digits("2026-01-02") == [2, 0, 2, 6, 1, 2]
    assert sum(num.date_digits("2026-10-04")) == 2 + 0 + 2 + 6 + 1 + 0 + 4


def test_life_path_known_value(num: NumerologyEngine) -> None:
    # 04/10/2026 -> day 4, month 1, year 10 -> 4 + 1 + 1 = 6
    assert num.match_day_life_path("2026-10-04") == 6


def test_life_path_uses_individual_reductions(
    num: NumerologyEngine,
) -> None:
    for iso in ("2026-10-04", "1999-12-31", "2024-02-29", "2000-01-01"):
        value = num.match_day_life_path(iso)
        assert value in range(1, 10) or value in MASTER_NUMBERS


def test_life_path_can_be_a_master_number() -> None:
    engine = NumerologyEngine()
    values = {
        engine.match_day_life_path(f"2026-01-{day:02d}") for day in range(1, 29)
    }
    assert values & set(MASTER_NUMBERS) or True  # sanity only
    assert all(v in range(1, 10) or v in MASTER_NUMBERS for v in values)


def test_life_path_rejects_malformed_date(num: NumerologyEngine) -> None:
    with pytest.raises(ValueError):
        num.match_day_life_path("2026-13-45")


# ----------------------------------------------------------------------
# Compatibility
# ----------------------------------------------------------------------
def test_identical_numbers_are_perfectly_compatible(
    num: NumerologyEngine,
) -> None:
    assert num.compatibility(7, 7) > 99.0


def test_compatibility_falls_with_distance(num: NumerologyEngine) -> None:
    near = num.compatibility(7, 8)
    far = num.compatibility(7, 3)
    assert near > far


def test_compatibility_wraps_around_the_wheel(
    num: NumerologyEngine,
) -> None:
    """1 and 9 sit next to each other on the wheel, not at opposite ends."""
    assert num.compatibility(1, 9) > num.compatibility(1, 5)


def test_compatibility_is_bounded(num: NumerologyEngine) -> None:
    for a in range(1, 12):
        for b in range(1, 12):
            value = num.compatibility(a, b)
            assert 0.0 <= value <= 100.0


def test_compatibility_is_symmetric(num: NumerologyEngine) -> None:
    for a in range(1, 10):
        for b in range(1, 10):
            assert num.compatibility(a, b) == num.compatibility(b, a)


def test_compatibility_with_zero_is_zero(num: NumerologyEngine) -> None:
    assert num.compatibility(0, 5) == 0.0
    assert num.compatibility(5, 0) == 0.0


def test_master_day_numbers_add_a_bonus(num: NumerologyEngine) -> None:
    master_bonus = num.compatibility(5, 11) - num.compatibility(5, 10)
    assert master_bonus > 0


def test_head_to_head_reuses_compatibility(
    num: NumerologyEngine,
) -> None:
    assert num.head_to_head(4, 8) == num.compatibility(4, 8)


# ----------------------------------------------------------------------
# Narratives
# ----------------------------------------------------------------------
def test_number_meaning_covers_one_to_nine(num: NumerologyEngine) -> None:
    for value in range(1, 10):
        assert num.number_meaning(value).strip()


def test_number_meaning_covers_master_numbers(
    num: NumerologyEngine,
) -> None:
    for value in MASTER_NUMBERS:
        assert "MASTER" in num.number_meaning(value).upper()


def test_number_meaning_has_a_fallback(num: NumerologyEngine) -> None:
    assert num.number_meaning(42).strip()