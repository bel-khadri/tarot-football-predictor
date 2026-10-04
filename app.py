"""Optional Streamlit web UI for the tarot + numerology football predictor.

Run with::

    streamlit run app.py
"""

from __future__ import annotations

import random
from datetime import date

import streamlit as st

from predictor import MatchPrediction, Predictor
from tarot_engine import TarotEngine

st.set_page_config(
    page_title="Tarot + Numerology Football Predictor",
    layout="wide",
)

PREDICT_KEY = "prediction"


# ----------------------------------------------------------------------
# Cached singletons
# ----------------------------------------------------------------------
@st.cache_resource
def get_engine() -> TarotEngine:
    return TarotEngine()


@st.cache_resource
def get_predictor(seed: int | None) -> Predictor:
    return Predictor(rng=random.Random(seed))


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def card_row(card: dict, index: int) -> None:
    """Render one drawn card."""
    orientation_colour = "#2E7D32" if card["orientation"] == "Upright" else "#C62828"
    with st.container(border=True):
        head, meta = st.columns([3, 1])
        head.markdown(f"**{index}. {card['display_name']}**")
        head.caption(card["position"] or "")
        meta.markdown(
            f"<div style='text-align:right'><b>{card['score']:.0f}</b>"
            f"<br/><span style='font-size:0.75rem'>effective power</span></div>",
            unsafe_allow_html=True,
        )
        st.caption(f"{card['role']} / {card['element']}")
        st.markdown(f"*{card['sports_meaning']}*")
        st.caption(
            f"Base {card['base_power']} x {card['polarity_multiplier']} "
            f"= {card['score']:.1f}"
        )
        st.markdown(
            f":{'green' if card['orientation'] == 'Upright' else 'red'}"
            f"[{card['orientation']}]",
        )


def team_panel(reading: dict, prefix: str) -> None:
    """Full detail panel for one team."""
    profile = reading["profile"]
    st.subheader(f"{reading['name']} - card energy")

    cols = st.columns(len(reading["cards"]))
    for index, (col, card) in enumerate(zip(cols, reading["cards"]), start=1):
        with col:
            card_row(card, index)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Attack", f"{profile['attack_strength']:.0f}")
    m2.metric("Defence", f"{profile['defence_strength']:.0f}")
    m3.metric("Midfield", f"{profile['midfield_strength']:.0f}")
    m4.metric("Strategy", f"{profile['strategy_strength']:.0f}")

    st.markdown(
        f"**Spread power:** {profile['total_power']:.1f} "
        f"(synergy bonus {profile['synergy_bonus']:.1f})"
    )
    st.info(profile["suit_narrative"])

    with st.expander("Full card-by-card explanation"):
        st.markdown(reading["explanation"])

    with st.expander("Goal derivation"):
        st.write(reading["goal_basis"])


def comparison_matrix(prediction: MatchPrediction) -> None:
    """The side-by-side Tarot vs Numerology matrix from the spec."""
    a = prediction.reading_a
    b = prediction.reading_b
    num = prediction.numerology
    card = prediction.match_card

    st.markdown("#### Side-by-side comparison matrix")
    st.table(
        {
            "Feature / Metric": [
                "Team A Energy",
                "Team B Energy",
                "Match Day Vibe",
                "Predicted Goal Range",
                "Full Card Explanations",
                "Final Consensus",
            ],
            "Tarot Analysis": [
                "Cards: "
                + "; ".join(c.display_name for c in a.cards)
                + f" | Base power {sum(c.base_power for c in a.cards)}"
                + f" | Effective {a.profile.total_power:.1f}"
                + f" | ATK {a.profile.attack_strength:.0f}"
                + f" / DEF {a.profile.defence_strength:.0f}",
                "Cards: "
                + "; ".join(c.display_name for c in b.cards)
                + f" | Base power {sum(c.base_power for c in b.cards)}"
                + f" | Effective {b.profile.total_power:.1f}"
                + f" | ATK {b.profile.attack_strength:.0f}"
                + f" / DEF {b.profile.defence_strength:.0f}",
                f"{card.display_name} [{card.element} / {card.role}] - "
                f"{card.sports_meaning}",
                f"{a.primary_goals} goal(s), range {a.goal_range[0]}-{a.goal_range[1]}, "
                f"xG {a.expected_goals:.2f} vs "
                f"{b.primary_goals} goal(s), range {b.goal_range[0]}-{b.goal_range[1]}, "
                f"xG {b.expected_goals:.2f}",
                "See the expandable explanation under each team above.",
                f"Card verdict: {prediction.tarot_winner} "
                f"({prediction.score_a:.1f} vs {prediction.score_b:.1f})",
            ],
            "Numerology Analysis": [
                f"Expression {a.expression_number} "
                f"(sum {a.expression_total}, Chaldean {a.chaldean_number}) | "
                f"Compatibility {a.compatibility:.0f}/100",
                f"Expression {b.expression_number} "
                f"(sum {b.expression_total}, Chaldean {b.chaldean_number}) | "
                f"Compatibility {b.compatibility:.0f}/100",
                f"Life Path {num.life_path} - {num.life_path_meaning} | "
                f"Harmony {num.harmony:.0f}/100",
                f"Numerology bias shifts A by {num.goal_bias:+.2f} "
                f"and B by {-num.goal_bias:+.2f} expected goals",
                "Full numerology narrative below the matrix.",
                f"Numerology verdict: {prediction.numerology_winner}",
            ],
        }
    )


def render_prediction(prediction: MatchPrediction) -> None:
    a = prediction.reading_a
    b = prediction.reading_b

    headline, sub = st.columns([3, 2])
    with headline:
        st.metric(
            "Predicted score",
            f"{a.primary_goals} - {b.primary_goals}",
        )
        st.markdown(f"### Consensus: {prediction.consensus_winner}")
    with sub:
        st.metric("Confidence", f"{prediction.confidence:.1f} pts")
        st.metric(
            "Win / Draw",
            f"{prediction.winner_probability:.0f}% / {prediction.draw_probability:.0f}%",
        )

    st.info(prediction.verdict_reasoning)

    match_tab, numerology_tab = st.tabs(["Match Day Card", "Numerology"])
    with match_tab:
        card_row(prediction.match_card.to_dict(), 1)
        st.markdown(
            f"**General reading:** {prediction.match_card.meaning}"
        )
    with numerology_tab:
        st.write(prediction.numerology.narrative)

    comparison_matrix(prediction)

    left, right = st.columns(2)
    with left:
        team_panel(a.to_dict(), "a")
    with right:
        team_panel(b.to_dict(), "b")


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
def sidebar() -> tuple:
    with st.sidebar:
        st.header("Match setup")
        team_a = st.text_input("Home team", value="Arsenal")
        team_b = st.text_input("Away team", value="Chelsea")
        match_date = st.date_input(
            "Match date",
            value=date.today(),
            min_value=date(1900, 1, 1),
            max_value=date(2100, 12, 31),
        )
        seed = st.number_input(
            "Random seed (leave 0 for a fresh draw)",
            min_value=0,
            value=0,
            step=1,
        )
        st.divider()
        st.subheader("Spread settings")
        reversal = st.slider(
            "Reversal chance (%)",
            min_value=0,
            max_value=100,
            value=35,
            step=5,
        )
        st.caption(
            "How often a card lands reversed. Reversed cards count for half "
            "their base power. 35% is the traditional third-of-the-deck rate."
        )
        read = st.button("Read the cards", type="primary", use_container_width=True)
        return team_a, team_b, match_date, seed, reversal / 100.0, read


def deck_browser() -> None:
    with st.expander("Deck reference (all 78 cards)"):
        engine = get_engine()
        suits = ["major_arcana", "wands", "cups", "swords", "pentacles"]
        selected = st.selectbox("Suit", suits, key="deck_suit")

        for card in engine.cards:
            if selected == "major_arcana":
                if card["arcana"] != "major":
                    continue
            elif card["suit"] != selected:
                continue

            with st.container(border=True):
                st.markdown(
                    f"**{card['name']}** "
                    f"<span style='color:gray'>({card['element']}, "
                    f"power {card['base_power']})</span>",
                    unsafe_allow_html=True,
                )
                st.caption(f"Upright: {card['sports_upright']}")
                st.caption(f"Reversed: {card['sports_reversed']}")


def main() -> None:
    st.title("Tarot + Numerology Football Predictor")
    st.caption(
        "A 78-card Rider-Waite spread and Pythagorean/Chaldean numerology, "
        "combined into a goal range and a verdict."
    )

    team_a, team_b, match_date, seed, reversal, read = sidebar()

    if read or PREDICT_KEY not in st.session_state:
        if not team_a.strip() or not team_b.strip():
            st.warning("Enter both team names to receive a reading.")
            return
        predictor = get_predictor(int(seed) or None)
        prediction = predictor.predict(
            team_a, team_b, match_date.isoformat()
        )
        st.session_state[PREDICT_KEY] = prediction

    render_prediction(st.session_state[PREDICT_KEY])
    deck_browser()


if __name__ == "__main__":
    main()