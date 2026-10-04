# Tarot + Numerology Football Predictor

A modular Python application that forecasts football results by combining a full
78-card Rider-Waite tarot spread with Pythagorean and Chaldean numerology.

The two systems are scored independently, then reconciled into a consensus
verdict, a goal range, and a full written explanation of every card.

> This is a deterministic entertainment/analysis tool. It is not a betting
> system and produces no real predictive edge.

## Requirements

Python 3.10+ for the core application. There are no runtime dependencies for
the CLI or the library - everything uses the standard library.

The optional web UI needs Streamlit:

```bash
pip install -r requirements.txt
```

## Quick start (CLI)

```bash
python main.py "Arsenal" "Chelsea" "2026-10-04"
```

Useful flags:

| Flag | Effect |
| --- | --- |
| `--seed N` | Deterministic draw; the same seed always gives the same reading |
| `--brief` | Skip the long card-by-card explanation |
| `--json` | Machine-readable output |
| `--card "The Tower"` | Print one card's upright and reversed readings |
| `--deck` | List all 78 cards |

## Optional web UI

```bash
streamlit run app.py
```

The sidebar controls both teams, the match date, a random seed, and the reversal
rate (the traditional third-of-the-deck rate is 35%).

## How the model works

### 1. Card power

Each card carries a base power from 1-100. The effective power is:

```
(base power * polarity multiplier) + elemental synergy bonus
```

An upright card has a `1.0` multiplier; a reversed card has `0.5`. The synergy
bonus rewards coherent spreads - cards sharing an element or a suit reinforce
each other.

### 2. Element roles

| Element | Football role |
| --- | --- |
| Fire | Attack |
| Earth | Defence |
| Water | Midfield / flow |
| Air | Strategy |

### 3. Goal expectation

A team's expected goals combine its attack strength, the opponent's defensive
strength, the suit profile, and the match-day numerology bias. The dominant
suit shifts the tempo: Wands raise the line, Pentacles lower it.

### 4. Numerology

- **Life Path** is derived from the match date, preserving Master Numbers 11,
  22 and 33.
- **Expression numbers** are the reduced letter sums of each team name, using
  both the Pythagorean and Chaldean maps.
- **Compatibility** compares a team's number against the match day on a 1-9
  wheel, so 1 and 9 sit next to each other while 1 and 5 sit opposite.

### 5. Consensus

If both systems agree, that verdict stands. If they disagree, the tie is broken
by the card score - unless the match card is reversed, in which case the
reading is called a draw.

## Project layout

| File | Purpose |
| --- | --- |
| `build_deck.py` | Regenerates `tarot_deck.json` |
| `tarot_deck.json` | The full 78-card dataset |
| `tarot_engine.py` | Card loading, drawing, scoring and `explain_draw` |
| `numerology_engine.py` | Life Path, Expression numbers, compatibility |
| `predictor.py` | Combines both systems into a match prediction |
| `main.py` | Command-line interface and comparison matrix |
| `app.py` | Optional Streamlit UI |
| `verify_app.py` | Exercises the UI without installing Streamlit |
| `tests/` | Test suite |

### Extending the deck

Edit `build_deck.py` and regenerate the dataset:

```bash
python build_deck.py
```

## Tests

```bash
python -m pytest
```

The suite covers deck integrity, the power formula, draw determinism, the
compatibility wheel, goal ranges, verdict logic, the CLI, and the UI's data
plumbing. A fuzz test runs 60 predictions and asserts that no result can be
internally inconsistent.