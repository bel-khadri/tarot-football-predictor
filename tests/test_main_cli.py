"""Tests for the CLI surface in ``main.py``."""

from __future__ import annotations

import json
import random

import pytest

import main
from predictor import Predictor


def test_parser_defaults() -> None:
    args = main.build_parser().parse_args([])
    assert args.team_a == "Team A"
    assert args.team_b == "Team B"
    assert args.match_date is None
    assert args.json is False
    assert args.brief is False


def test_parser_reads_positional_arguments() -> None:
    args = main.build_parser().parse_args(["Arsenal", "Chelsea", "2026-10-04"])
    assert args.team_a == "Arsenal"
    assert args.team_b == "Chelsea"
    assert args.match_date == "2026-10-04"


def test_parser_reads_flags() -> None:
    args = main.build_parser().parse_args(
        ["--seed", "42", "--json", "--brief", "A", "B"]
    )
    assert args.seed == 42
    assert args.json is True
    assert args.brief is True


def test_render_matrix_contains_every_required_row() -> None:
    predictor = Predictor(rng=random.Random(3))
    result = predictor.predict("Arsenal", "Chelsea", "2026-10-04")
    text = main.render_matrix(result)
    for section in (
        "TEAM A ENERGY",
        "TEAM B ENERGY",
        "MATCH DAY VIBE",
        "PREDICTED GOAL RANGES",
        "FINAL CONSENSUS",
        "TAROT ANALYSIS",
        "NUMEROLOGY ANALYSIS",
    ):
        assert section in text, section


def test_render_matrix_shows_both_teams_and_scores() -> None:
    predictor = Predictor(rng=random.Random(3))
    result = predictor.predict("Arsenal", "Chelsea", "2026-10-04")
    text = main.render_matrix(result)
    assert "Arsenal" in text
    assert "Chelsea" in text
    assert "Predicted score" in text
    assert result.consensus_winner.upper() in text.upper()


def test_render_numerology_narrative_mentions_life_path() -> None:
    predictor = Predictor(rng=random.Random(3))
    result = predictor.predict("Arsenal", "Chelsea", "2026-10-04")
    text = main.render_numerology_narrative(result)
    assert str(result.numerology.life_path) in text


def test_render_explanations_includes_both_teams() -> None:
    predictor = Predictor(rng=random.Random(3))
    result = predictor.predict("Arsenal", "Chelsea", "2026-10-04")
    text = main.render_explanations(result)
    assert result.team_a in text
    assert result.team_b in text


def test_main_json_output_is_valid(capsys) -> None:
    exit_code = main.main(
        ["--seed", "11", "--json", "Arsenal", "Chelsea", "2026-10-04"]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["team_a"] == "Arsenal"
    assert payload["team_b"] == "Chelsea"


def test_main_text_output_exits_zero(capsys) -> None:
    exit_code = main.main(["--seed", "11", "--brief", "Arsenal", "Chelsea",
                           "2026-10-04"])
    assert exit_code == 0
    assert "FINAL CONSENSUS" in capsys.readouterr().out


def test_main_rejects_a_bad_date(capsys) -> None:
    exit_code = main.main(["Arsenal", "Chelsea", "04-10-2026"])
    assert exit_code == 2
    assert "error" in capsys.readouterr().err


def test_main_card_lookup(capsys) -> None:
    assert main.main(["--card", "The Tower"]) == 0
    out = capsys.readouterr().out
    assert "The Tower (upright)" in out
    assert "The Tower (reversed)" in out
    assert "Base power" in out


def test_main_card_lookup_reports_unknown_cards(capsys) -> None:
    with pytest.raises(KeyError):
        main.main(["--card", "Nonexistent Card"])


def test_main_deck_listing(capsys) -> None:
    assert main.main(["--deck"]) == 0
    out = capsys.readouterr().out
    assert "Deck size: 78" in out
    assert "The Fool" in out
    assert "Ace of Wands" in out


def test_main_is_reproducible_with_a_seed(capsys) -> None:
    main.main(["--seed", "99", "--json", "A", "B", "2026-10-04"])
    first = capsys.readouterr().out
    main.main(["--seed", "99", "--json", "A", "B", "2026-10-04"])
    second = capsys.readouterr().out
    assert first == second


def test_output_has_no_unicode_replacement_characters() -> None:
    """The Windows console must not mangle the narrative text."""
    predictor = Predictor(rng=random.Random(3))
    result = predictor.predict("Arsenal", "Chelsea", "2026-10-04")
    for text in (
        main.render_matrix(result),
        main.render_numerology_narrative(result),
        main.render_explanations(result),
        result.reading_a.explanation,
    ):
        assert "\ufffd" not in text
        assert all(ord(ch) < 128 for ch in text), "non-ASCII character in output"