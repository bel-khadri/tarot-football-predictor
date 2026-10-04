"""CLI entry point for the Tarot + Numerology football predictor.

Usage::

    python main.py "Arsenal" "Chelsea" 2026-10-04
    python main.py --seed 42 --json "Real Madrid" "Barcelona"
    python main.py --card The Tower --explain-only
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from typing import List, Optional, Sequence

from predictor import MatchPrediction, Predictor
from tarot_engine import TarotEngine, explain_card

WIDTH = 78


def _rule(char: str = "-") -> str:
    return char * WIDTH


def _header(title: str) -> str:
    """Print and return a banner block."""
    block = f"\n{_rule('=')}\n{title.center(WIDTH)}\n{_rule('=')}"
    print(block)
    return block


def _wrap(text: str, indent: int = 18, width: int = WIDTH) -> str:
    """Lightweight wrapper so long narratives stay inside the matrix."""
    import textwrap

    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    return "\n".join(
        textwrap.wrap(
            cleaned,
            width=max(20, width - indent),
            initial_indent=" " * indent,
            subsequent_indent=" " * indent,
        )
    )


def render_matrix(prediction: MatchPrediction) -> str:
    """The side-by-side Tarot vs Numerology comparison output matrix."""
    lines: List[str] = []
    a = prediction.reading_a
    b = prediction.reading_b
    num = prediction.numerology
    card = prediction.match_card

    _header(f"  {prediction.team_a}  vs  {prediction.team_b}   ({prediction.match_date})")
    lines.append("")

    # ---- Row: Team A energy ------------------------------------------
    lines.append(_rule())
    lines.append(f"{'Feature / Metric':<26}| {'TAROT ANALYSIS':<26}| NUMEROLOGY ANALYSIS")
    lines.append(_rule())
    lines.append("")

    lines.append("TEAM A ENERGY")
    a_cards = "; ".join(c.display_name for c in a.cards)
    a_power = (
        f"base {sum(c.base_power for c in a.cards)} / "
        f"effective {a.profile.total_power:.1f}"
    )
    a_split = (
        f"ATK {a.profile.attack_strength:.0f} | DEF {a.profile.defence_strength:.0f} | "
        f"MID {a.profile.midfield_strength:.0f} | STR {a.profile.strategy_strength:.0f}"
    )
    a_num = (
        f"Expression {a.expression_number} (sum {a.expression_total}, "
        f"Chaldean {a.chaldean_number}) | Compatibility {a.compatibility:.0f}/100"
    )
    lines.append(f"  Cards drawn   : {a_cards}")
    lines.append(f"  Card power    : {a_power}")
    lines.append(_wrap(f"Breakdown: {a_split}"))
    lines.append(_wrap(f"Numerology: {a_num}"))
    lines.append("")

    # ---- Row: Team B energy ------------------------------------------
    lines.append(_rule())
    lines.append("TEAM B ENERGY")
    b_cards = "; ".join(c.display_name for c in b.cards)
    b_power = (
        f"base {sum(c.base_power for c in b.cards)} / "
        f"effective {b.profile.total_power:.1f}"
    )
    b_split = (
        f"ATK {b.profile.attack_strength:.0f} | DEF {b.profile.defence_strength:.0f} | "
        f"MID {b.profile.midfield_strength:.0f} | STR {b.profile.strategy_strength:.0f}"
    )
    b_num = (
        f"Expression {b.expression_number} (sum {b.expression_total}, "
        f"Chaldean {b.chaldean_number}) | Compatibility {b.compatibility:.0f}/100"
    )
    lines.append(f"  Cards drawn   : {b_cards}")
    lines.append(f"  Card power    : {b_power}")
    lines.append(_wrap(f"Breakdown: {b_split}"))
    lines.append(_wrap(f"Numerology: {b_num}"))
    lines.append("")

    # ---- Row: Match day vibe -----------------------------------------
    lines.append(_rule())
    lines.append("MATCH DAY VIBE")
    lines.append(
        f"  Tarot         : {card.display_name} [{card.element} / {card.role}]"
    )
    lines.append(_wrap(f"                  {card.sports_meaning}"))
    lines.append(_wrap(f"Numerology: Life Path {num.life_path} - {num.life_path_meaning}"))
    lines.append(_wrap(f"Harmony between names: {num.harmony:.0f}/100"))
    lines.append("")

    # ---- Row: Goal ranges --------------------------------------------
    lines.append(_rule())
    lines.append("PREDICTED GOAL RANGES")
    lines.append(
        f"  {prediction.team_a}: {a.primary_goals} goal"
        f"{'s' if a.primary_goals != 1 else ''} "
        f"(range {a.goal_range[0]}-{a.goal_range[1]}), "
        f"xG {a.expected_goals:.2f}"
    )
    lines.append(_wrap(f"                  Basis: {a.goal_basis}"))
    lines.append(
        f"  {prediction.team_b}: {b.primary_goals} goal"
        f"{'s' if b.primary_goals != 1 else ''} "
        f"(range {b.goal_range[0]}-{b.goal_range[1]}), "
        f"xG {b.expected_goals:.2f}"
    )
    lines.append(_wrap(f"                  Basis: {b.goal_basis}"))
    lines.append(f"  Predicted score: {prediction.predicted_goals_a} - "
                 f"{prediction.predicted_goals_b}")
    lines.append("")

    # ---- Row: Final consensus ----------------------------------------
    lines.append(_rule())
    lines.append("FINAL CONSENSUS")
    lines.append(
        f"  Card verdict  : {prediction.tarot_winner}  "
        f"(scores {prediction.score_a:.1f} vs {prediction.score_b:.1f})"
    )
    lines.append(f"  Number verdict: {prediction.numerology_winner}")
    lines.append(f"  Consensus     : {prediction.consensus_winner.upper()}")
    lines.append(
        f"  Confidence    : {prediction.confidence:.1f} pts | "
        f"win {prediction.winner_probability:.0f}% / "
        f"draw {prediction.draw_probability:.0f}%"
    )
    lines.append(_wrap(f"  Reasoning     : {prediction.verdict_reasoning}"))
    lines.append(_rule())

    return "\n".join(lines)


def render_numerology_narrative(prediction: MatchPrediction) -> str:
    lines = ["", _header("  NUMEROLOGY: FULL NARRATIVE"), ""]
    lines.append(_wrap(prediction.numerology.narrative))
    return "\n".join(lines)


def render_explanations(prediction: MatchPrediction) -> str:
    lines = ["", _header("  FULL CARD EXPLANATIONS"), ""]
    for reading in (prediction.reading_a, prediction.reading_b):
        lines.append(reading.explanation)
        lines.append("")
        lines.append(_rule())
        lines.append("")
    return "\n".join(lines)


def render_card_reference(card_name: str) -> str:
    """Print the full interpretation record for a single named card."""
    engine = TarotEngine()
    raw = engine.find_card(card_name)
    for orientation in ("upright", "reversed"):
        print(f"  {raw['name']} ({orientation})")
        print(f"    Element      : {raw['element']}")
        print(f"    Base power   : {raw['base_power']}/100")
        print(f"    General      : {raw[f'{orientation}_meaning']}")
        print(f"    Sports       : {raw[f'sports_{orientation}']}")
        print()
    return ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tarot-football-predictor",
        description=(
            "Predict a football result by combining a 78-card tarot reading "
            "with Pythagorean/Chaldean numerology."
        ),
    )
    parser.add_argument("team_a", nargs="?", default="Team A")
    parser.add_argument("team_b", nargs="?", default="Team B")
    parser.add_argument(
        "match_date",
        nargs="?",
        default=None,
        help="Match date as YYYY-MM-DD (defaults to today).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed the RNG for reproducible readings.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the full prediction as JSON instead of the text matrix.",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Show the summary matrix only, without the long narratives.",
    )
    parser.add_argument(
        "--card",
        type=str,
        default=None,
        help="Print the interpretation record for a single card and exit.",
    )
    parser.add_argument(
        "--deck",
        action="store_true",
        help="List the deck contents and exit.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.card:
        render_card_reference(args.card)
        return 0

    if args.deck:
        engine = TarotEngine()
        print(f"Deck size: {engine.deck_size}")
        for card in engine.cards:
            print(
                f"  {card['name']:<24} {card['element']:<6} "
                f"power {card['base_power']:>3}  [{card['arcana']}]"
            )
        return 0

    rng = random.Random(args.seed)
    predictor = Predictor(rng=rng)

    try:
        prediction = predictor.predict(args.team_a, args.team_b, args.match_date)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(prediction.to_dict(), indent=2, ensure_ascii=False))
        return 0

    print(render_matrix(prediction))
    if not args.brief:
        print(render_numerology_narrative(prediction))
        print(render_explanations(prediction))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())