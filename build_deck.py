"""Regenerate ``tarot_deck.json`` - the full 78-card Rider-Waite deck.

Every card carries a base power rating (1-100), an elemental association and
four interpretation strings: general upright/reversed plus a sports-context
upright/reversed reading.

Run with::

    python build_deck.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

DECK_PATH = Path(__file__).parent / "tarot_deck.json"

# --------------------------------------------------------------------------
# Major Arcana - (name, element, base_power, upright, reversed, sports_up, sports_rev)
# --------------------------------------------------------------------------
MAJOR_ARCANA: List[tuple] = [
    (
        "The Fool", "Air", 75,
        "New beginnings, innocence, leap of faith",
        "Recklessness, naivety, folly",
        "Fresh legs and fearless attacking; a debutant or returning player "
        "who treats the occasion with wide-eyed confidence",
        "Overconfidence; a rookie's stray pass or reckless challenge hands "
        "the opposition a free chance",
    ),
    (
        "The Magician", "Fire", 90,
        "Manifestation, resourcefulness, raw talent",
        "Manipulation, poor planning, talent wasted",
        "A creative hub in full flow - a maverick finalising chances and "
        "exploiting the opponent's weakest defender",
        "Trying to be the hero; showboating and overcomplicated passes break "
        "the team's rhythm",
    ),
    (
        "The High Priestess", "Water", 85,
        "Intuition, mystery, the unspoken",
        "Secrets, disconnection, ignored signals",
        "Exceptional defensive discipline and game-reading; the back four "
        "knows every trigger before the striker moves",
        "A shape nobody understands; defensive comms break down and marking "
        "is lost in midfield",
    ),
    (
        "The Empress", "Earth", 85,
        "Nurture, abundance, fertile ground",
        "Stagnation, smothering, dependence",
        "Patient possession built from the back, patiently probing until a gap "
        "opens; also a productive academy",
        "Sterile, slow possession with no cutting edge; over-engineered "
        "attacks that never reach the box",
    ),
    (
        "The Emperor", "Fire", 90,
        "Authority, structure, command",
        "Tyranny, rigidity, domineering control",
        "A captain or manager who stamps authority on the pitch; disciplined "
        "shape, clear roles, total organisation",
        "Stubborn tactics with no plan B; forcing a fit player out of his "
        "natural role",
    ),
    (
        "The Hierophant", "Earth", 80,
        "Tradition, doctrine, the tried and tested",
        "Rebellion, heresy, refusal to adapt",
        "A well-drilled system doing exactly what it has done a hundred times; "
        "experience and set-piece superiority",
        "Clinging to a failing approach; the opposition's variations expose "
        "every outdated habit",
    ),
    (
        "The Lovers", "Air", 80,
        "Union, harmony, chosen partnership",
        "Discord, imbalance, broken rapport",
        "Telepathic chemistry - a midfielder and a striker who finish each "
        "other's movements; combinations that look rehearsed",
        "Cliques in the dressing room and miscommunication on the pitch; "
        "passes that die in crowded areas",
    ),
    (
        "The Chariot", "Fire", 95,
        "Willpower, momentum, hard-won victory",
        "Aggression without direction, defeat, loss of control",
        "Relentless forward momentum - the team that refuses to be pinned and "
        "keeps driving at the throat of the defence",
        "Reckless over-committing with the whole team upfield; permanent "
        "gaps exploited at the counter",
    ),
    (
        "Strength", "Fire", 95,
        "Courage, patience, gentle mastery",
        "Weakness, self-doubt, brittle nerve",
        "Mental resilience; holding a lead under sustained pressure and "
        "dominating physically through the middle third",
        "Cracking under pressure; legs going and heads dropping the moment "
        "the game swings",
    ),
    (
        "The Hermit", "Earth", 70,
        "Solitude, inner search, quiet counsel",
        "Isolation, withdrawal, purposelessness",
        "Careful build-up, probing and patience - soaking up pressure while "
        "waiting for one clear opening",
        "Too passive to hurt anyone; deep and inert, waiting for a game that "
        "will never arrive",
    ),
    (
        "Wheel of Fortune", "Fire", 90,
        "Cycles, turning points, fate",
        "Bad luck, fated setbacks, resisted change",
        "The momentum swing belongs to them - a deflection, a lucky bounce and "
        "a completely different game after the interval",
        "Own goals, deflections and refereeing decisions all going the wrong "
        "way at the crucial moment",
    ),
    (
        "Justice", "Air", 85,
        "Balance, fairness, clear judgement",
        "Unfairness, bias, evasion of accountability",
        "Disciplined, legal defending; decisions won cleanly, no bookings, "
        "perfect tactical balance",
        "Discipline collapses - bookings, dissent, a red card and a VAR "
        "argument that costs the team its shape",
    ),
    (
        "The Hanged Man", "Water", 65,
        "Pause, surrender, new perspective",
        "Stalling, resistance, wasted sacrifice",
        "A tactical reset mid-game; absorbing pressure, changing system and "
        "becoming a different team after the break",
        "A parked bus with no route out; time-wasting that only deepens the "
        "hole the team is already in",
    ),
    (
        "Death", "Water", 90,
        "Endings, transformation, irreversible change",
        "Clinging on, resistance, stalled decay",
        "The game-killing goal; a transformation that shuts the contest "
        "down and drains the opponent's belief",
        "A late collapse; a thrown-away lead, legs gone in the final "
        "quarter, the game dying when it was theirs",
    ),
    (
        "Temperance", "Fire", 80,
        "Balance, moderation, measured patience",
        "Excess, imbalance, lopsidedness",
        "Perfectly calibrated football - attack and defence in exact "
        "proportion, tempo always under control",
        "A lopsided team that either overruns itself or parks the bus with no "
        "middle ground",
    ),
    (
        "The Devil", "Earth", 85,
        "Bondage, compulsion, material appetite",
        "Liberation, released from the trap",
        "Ruthless, suffocating pressure; opponents pinned in their own half, "
        "psychological warfare winning the war of wills",
        "The team walking into the opponent's trap - self-sabotage, loss of "
        "discipline, desire overriding the game plan",
    ),
    (
        "The Tower", "Fire", 95,
        "Sudden upheaval, collapse, revelation",
        "Disaster narrowly avoided, fear of change",
        "The upheaval arrives in the box: a collision, an injury, a goal that "
        "changes everything - or a back line that simply caves in",
        "Disaster hanging by a thread; surviving through damage limitation "
        "and sheer luck",
    ),
    (
        "The Star", "Air", 90,
        "Hope, faith, quiet inspiration",
        "Despair, lost belief, the light fading",
        "The moment the stadium lifts - one inspirational strike or heroic save "
        "that turns belief back on",
        "Heads dropping in unison; the team stops believing in what it is "
        "attempting",
    ),
    (
        "The Moon", "Water", 75,
        "Illusion, fear, things unseen",
        "Confusion lifting, deception exposed",
        "Deception and misdirection; a shape that keeps the opposition "
        "guessing, playing a different shape to the one they scouted",
        "The fog lifts and the game is suddenly clear; the team adapts and "
        "starts seeing the trap",
    ),
    (
        "The Sun", "Fire", 98,
        "Joy, vitality, unambiguous success",
        "Glare, frustration, talent under a cloud",
        "Peak form with everything clicking - the attacking day, the "
        "free-flowing goals, the inevitable win",
        "Frustration with chances going begging; a team playing well enough "
        "but unable to finish",
    ),
    (
        "Judgement", "Fire", 90,
        "Awakening, reckoning, redemption",
        "Self-doubt, hesitation, a moment refused",
        "The redemption arc completed; a player atoning for past errors with "
        "the decisive intervention in a huge moment",
        "Second-guessing in front of goal; the chance taken twice and buried "
        "twice",
    ),
    (
        "The World", "Earth", 98,
        "Completion, integration, the summit",
        "Unfinished business, the summit missed",
        "Total football; a complete performance that closes out the tie and "
        "claims the trophy",
        "So close it hurts - a dropped ball at the death, a point surrendered "
        "from a winning position",
    ),
]

# --------------------------------------------------------------------------
# Minor Arcana - rank, base_power, upright, reversed, sports_up, sports_rev
# --------------------------------------------------------------------------
SUIT_ARCANA: Dict[str, tuple] = {
    "wands": (
        "Fire",
        "Energy, drive, raw attacking force",
        [
            ("Ace", 88, "A new creative spark; pure drive",
             "False starts; a promising move that comes to nothing",
             "A strike from outside the box or a dribble that beats three - a "
             "genuine spark of attacking intent",
             "A promising attack that is mislaid repeatedly; sterile possession "
             "in the final third"),
            ("Two", 76, "Planning, choice, will held in check",
             "Fear, indecision, a plan abandoned",
             "A rehearsed attack rehearsed once too often; the second attempt "
             "is telegraphed",
             "Options at the feet of the attacker and none of them taken"),
            ("Three", 84, "Expansion, foresight, waiting to ship out",
             "Delays, frustration, an over-played hand",
             "Excellent scouting of the opposition; the counter-attack that "
             "should have been pulled two moves earlier",
             "Hesitation in the box; the final pass delayed until the moment "
             "has gone"),
            ("Four", 72, "Celebration, homecoming, a settled hearth",
             "Instability, unrest, a wobbly platform",
             "A goal lifted the mood and lifted the team; the home crowd "
             "becomes a seventh attacker",
             "Scorer silenced; unstable dressing room and a lead that stops "
             "being safe"),
            ("Five", 80, "Fierce competition, healthy rivalry",
             "Pointless conflict, squabbling",
             "Competitive edge without losing discipline; the duels the team "
             "needs to win",
             "Cards flying in a needless scrap; a melee that costs the better "
             "player"),
            ("Six", 82, "Victory earned, public recognition",
             "Vain glory, an unearned win",
             "A deserved, well-worked goal; the recognition that follows "
             "raises the confidence further",
             "Celebrating a goal that should not have been conceded"),
            ("Seven", 74, "Defence of hard-won ground, standing firm",
             "Overwhelmed, giving up the high ground",
             "A stubborn, well-drilled defensive block that refuses to be "
             "broken down",
             "The block collapses once the pressure is sustained"),
            ("Eight", 86, "Swift arrival, news moving fast",
             "Delayed news, a stalled attack",
             "A rapid counter-attack launched the instant possession is won",
             "The break never comes; the move stalls in midfield"),
            ("Nine", 70, "Guarded resilience, the last stand",
             "Exhaustion, walls closing in, paranoia",
             "Battered but still upright; the team holds on through sheer "
             "grit against waves of attacks",
             "Fatally gassed; the back line starts giving ground"),
            ("Ten", 92, "Overload, too much to carry, collapse under load",
             "Burden lifted, delegation finally accepted",
             "Everyone contributes and the workload overwhelms the opposition "
             "- or the squad, whichever lasts",
             "The burden shared; fatigue turned into a collective push"),
            ("Page", 68, "Curiosity, an eager messenger",
             "Immaturity, unreliable news",
             "A fearless young substitute or academy player injecting energy",
             "Raw inexperience; the hopeful ball that is overhit"),
            ("Knight", 88, "Bold adventure, charges mounted",
             "Rashness, volatility, poor follow-through",
             "The pacy forward who bursts into space and terrorises a "
             "defence that cannot handle him",
             "All pace and no thought; the cross sails out and the "
             "breakdown becomes a counter"),
            ("Queen", 90, "Warmth, confidence, magnetism",
             "Insecurity, jealousy, smothering heat",
             "A magnetic playmaker who drags the ball with her and lifts the "
             "whole stadium",
             "Emotional and self-doubting; the captain visibly unraveling"),
            ("King", 89, "Visionary leadership, natural authority",
             "Tyrannical, over-dominant",
             "The leader who organises the attack and demands standards from "
             "the front",
             "A leader who overruns his players and stifles the creativity "
             "around him"),
        ],
    ),
    "cups": (
        "Water",
        "Flow, emotion, the fluid midfield",
        [
            ("Ace", 92, "New love, the cup overflowing",
             "Emptiness, feeling blocked",
             "The emotional tide turns; a flowing attacking move and a goal "
             "that feels inevitable",
             "Feelings choked off; the passing that should flow dies at the "
             "feet"),
            ("Two", 78, "Partnership, meeting of equals",
             "Imbalance, a broken alliance",
             "The two strikers finally on the same wavelength; a single "
             "movement producing a chance",
             "The partnership breaks down; two strikers in each other's "
             "way"),
            ("Three", 83, "Celebration, friendship, shared joy",
             "Excess, over-indulgence, the group turns inwards",
             "Team morale at its highest; the third-man runs and shared joy "
             "on the touchline",
             "Cliques and in-fighting; the dressing room turns on itself"),
            ("Four", 68, "Contentment, apathy, an unasked question",
             "Awareness, emerging from apathy",
             "A team too comfortable with 1-0; the passive stretch that "
             "invites trouble",
             "The mood finally lifts; the spark that reignites the chase"),
            ("Five", 66, "Grief, spilled cups, regret",
             "Acceptance, moving on, forgiveness",
             "The crestfallen slump after conceding; heads down, body language "
             "dying",
             "The team shakes off the disappointment and gets back to work"),
            ("Six", 82, "Memory, nostalgia, the past returning",
             "Stuck in the past, idealising",
             "A return to a familiar, well-rehearsed pattern that works",
             "Dwelling on past glory instead of the game in front of them"),
            ("Seven", 72, "Illusion, wishful thinking, daydreams",
             "Clarity, options finally seen",
             "A team convinced of something that is not true - passing up "
             "the obvious chance",
             "The fog clears; the real shape of the game is finally visible"),
            ("Eight", 66, "Walking away, an offer declined",
             "Stagnation, aimless drifting",
             "The team that drifts from the contest, going through motions "
             "with nothing left",
             "Pulling the team back from the precipice; motivation found at "
             "the last moment"),
            ("Nine", 88, "Contentment, wish fulfilled, satisfaction",
             "Smugness, hollow fulfilment",
             "The satisfying sense of a job well done; a controlled, complete "
             "performance",
             "Complacency after taking the lead; satisfaction that breeds "
             "carelessness"),
            ("Ten", 90, "Harmony, emotional fulfilment, the happy ending",
             "Rupture, the picture shattered",
             "The squad playing as one; total emotional unity and a goal that "
             "caps everything",
             "Unity shattered; the emotional dressing room that falls apart"),
            ("Page", 67, "Tender message, an unexpected offer",
             "Immaturity, emotional immaturity",
             "A young creative given the freedom to express himself",
             "A fanciful youngster who chases the highlight reel instead of "
             "the instruction"),
            ("Knight", 86, "Romance, an offer made, an emotional charge",
             "Moodiness, empty promises",
             "The dribbling midfielder whose run and cross is pure inspiration",
             "Foolish promises that never become actual deliveries"),
            ("Queen", 94, "Compassion, intuition, deep emotional mastery",
             "Overgiving, smothering, emotional flooding",
             "The calm, empathetic leader who holds the team together under "
             "pressure and reads the game emotionally",
             "Emotion overruns judgement; decisions made on feeling alone"),
            ("King", 85, "Equanimity, counsel, calm authority",
             "Suppression, emotional manipulation",
             "The composed leader whose calm keeps a chaotic match settled",
             "Emotionally repressed; a coldness that unsettles the team"),
        ],
    ),
    "swords": (
        "Air",
        "Intellect, strategy, cutting precision",
        [
            ("Ace", 89, "Clarity, breakthrough, the cutting idea",
             "Confusion, a blunt instrument",
             "A precise, decisive strike that cuts the defence open - the "
             "moment of tactical clarity",
             "Confusion in the head; the shot blocked or the decision that "
             "makes no sense"),
            ("Two", 74, "Stalemate, a decision deferred",
             "False peace, information withheld",
             "A standoff between two tactical minds; possession contested "
             "without a way through",
             "Information finally shared and the stalemate broken"),
            ("Three", 80, "Heartbreak, the necessary pain",
             "Healing, the pain released",
             "The heartbreak of conceding - the shot that should have been "
             "saved and the silence after",
             "The wound closing; the team rallies after the blow"),
            ("Four", 66, "Rest, recovery, a deliberate pause",
             "Restlessness, burnout, waking too early",
             "A halftime regroup; the tactical switch that resets the match",
             "Forced rest becomes forced action; fatigue builds early"),
            ("Five", 70, "Conflict, hollow victory, dissension",
             "Forgiveness, moving past the spat",
             "Rowing in the dressing room or between the back four; the "
             "argument that costs concentration",
             "The spat ends; everyone back on the same page"),
            ("Six", 78, "Transition, moving on, the passage",
             "Stuck, unresolved baggage",
             "The transitional pass that launches the counter; the team moves "
             "on from a big chance missed",
             "Transition game abandoned; caught flat-footed by every break"),
            ("Seven", 72, "Strategy, stealth, a careful scheme",
             "Dishonesty, cunning out of control",
             "A well-worked scheme executed secretly - disguise, disguise, "
             "the trap sprung on the opposition",
             "The scheme is rumbled; deception that fools nobody, not least "
             "the team itself"),
            ("Eight", 84, "Restriction, self-binding, a narrowed pitch",
             "Release, new options opening",
             "A team hemmed in by the opposition's press and unable to free "
             "itself",
             "The tie breaks - suddenly the whole pitch opens up"),
            ("Nine", 64, "Anxiety, the 3am wake-up, dread",
             "Perspective, help on the way",
             "Nerve and dread before kick-off; the team visibly anxious and "
             "second-guessing",
             "The anxiety lifts; perspective returns and the mind settles"),
            ("Ten", 76, "Ruin, the final blow, defeat made total",
             "Recovery, slow repair",
             "The heavy defeat that exposes every structural flaw",
             "Recovery begins; the long walk back from 0-3"),
            ("Page", 69, "Curiosity, vigilance, the sharp question",
             "Hasty conclusions, scattered talk",
             "The eager young defender asking questions and reading the "
             "opposition",
             "Scattered, half-thought questioning that muddies the plan"),
            ("Knight", 88, "Charging intellect, decisive action",
             "Reckless aggression, blunt force",
             "The pressing forward who hunts the ball with relentless "
             "intelligence",
             "All charge and no thought; the foul that comes with the "
             "enthusiasm"),
            ("Queen", 87, "Clarity, honesty, cutting truth",
             "Cynicism, a bitter judgement, cruelty",
             "The honest, analytical voice in the dressing room who sees the "
             "game exactly as it is",
             "Cutting remarks that sour the team; judgement passed too "
             "harshly"),
            ("King", 90, "Intellectual mastery, principle, judgement",
             "Abuse of intellect, manipulation, tyranny",
             "The strategist at the helm; cold, clear decision-making and "
             "total tactical control",
             "Intellectual tyranny; the manager who overrules the pitch"),
        ],
    ),
    "pentacles": (
        "Earth",
        "Body, resources, the solid defensive block",
        [
            ("Ace", 86, "Opportunity, a solid foundation, new resources",
             "Lost opportunity, poor planning, wasted talent",
             "A grounded, well-built chance that should be converted; a solid "
             "platform for the whole team",
             "A goal that should have been taken wasted; a squad that leaves "
             "easy points on the pitch"),
            ("Two", 74, "Balance, juggling, careful planning",
             "Overload, dropped balls, disorganisation",
             "Two full-backs managing the flanks with practised balance, "
             "juggling duties without dropping a ball",
             "Duties dropped; the flanks are turned inside out"),
            ("Three", 82, "Craftsmanship, collaboration, skilled work",
             "Mismatched effort, poor coordination",
             "Every player executing the same plan precisely - set-piece "
             "choreography done right",
             "Everyone running but nobody agreeing; the drill that never "
             "clicks"),
            ("Four", 70, "Possession, security, holding what is yours",
             "Hoarding, complacency, reluctance to risk",
             "A compact block sitting on the ball and refusing to release it",
             "Possession becomes hoarding; the ball is never let go"),
            ("Five", 64, "Hardship, exclusion, the empty seat",
             "Recovery, help finally arriving",
             "A team cut off and struggling; nobody left out in the cold "
             "without a purpose",
             "Help finally comes; the outcast is brought back in"),
            ("Six", 80, "Generosity, balance, the scales weighed",
             "Strings attached, unequal exchange",
             "The fair exchange of effort for reward; a well-balanced squad "
             "sharing the load",
             "The scales tipped; a star carrying a team that gives him "
             "nothing"),
            ("Seven", 68, "Patience, persistence, long-term assessment",
             "Impatience, wasted effort, a poor return",
             "The long grind - working without reward and refusing to "
             "abandon the plan",
             "Patience runs out; the effort is spent on nothing"),
            ("Eight", 75, "Diligence, apprenticeship, mastery in progress",
             "Drudgery, procrastination, being strung along",
             "Grinding out the unglamorous work; set-piece routines repeated "
             "until automatic",
             "Mundane work left undone; the details that decide matches "
             "skipped"),
            ("Nine", 90, "Self-sufficiency, the reward of the work",
             "Comfortable complacency, isolation",
             "The rewards of a long campaign; a team enjoying the fruits of "
             "everything they built",
             "Comfort so complete that nobody bothers to defend it"),
            ("Ten", 96, "Legacy, the long game, permanence",
             "Fragile inheritance, the empire cracking",
             "The weight of expectation and history; defending an inherited "
             "legacy on the pitch",
             "The inheritance proved hollow; cracks appear under pressure"),
            ("Page", 68, "Study, a beginner's promise",
             "Procrastination, poor grounding",
             "The academy prospect doing his homework and finally delivering",
             "Grounding never laid; a raw talent with no fundamentals"),
            ("Knight", 84, "Methodical labour, slow and certain progress",
             "Stagnation, laziness, dull routine",
             "The unglamorous workhorse who covers every blade of grass and "
             "keeps the shape intact",
             "Dull routine; a team going through the motions"),
            ("Queen", 89, "Nurturing competence, practical wisdom",
             "Over-work, worry, neglecting oneself",
             "The calm, capable figure who runs the side and looks after the "
             "people in it",
             "Carrying the whole squad on tired shoulders"),
            ("King", 93, "Provision, mastery, secure command",
             "Rigidity, greed, inflexibility",
             "The solid bedrock - a dominant leader who makes the side "
             "impossible to shift",
             "Immovable and inflexible; the fortress that never modernises"),
        ],
    ),
}


def _build_major() -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for index, (name, element, power, up, rev, sports_up, sports_rev) in enumerate(
        MAJOR_ARCANA
    ):
        cards.append(
            {
                "id": f"major-{index:02d}",
                "name": name,
                "arcana": "major",
                "suit": None,
                "rank": name,
                "number": index,
                "element": element,
                "base_power": power,
                "upright_meaning": up,
                "reversed_meaning": rev,
                "sports_upright": sports_up,
                "sports_reversed": sports_rev,
            }
        )
    return cards


def _build_minor() -> Dict[str, List[Dict[str, Any]]]:
    suits: Dict[str, List[Dict[str, Any]]] = {}
    for suit, (element, _theme, ranks) in SUIT_ARCANA.items():
        cards: List[Dict[str, Any]] = []
        for number, (rank, power, up, rev, sports_up, sports_rev) in enumerate(
            ranks, start=1
        ):
            cards.append(
                {
                    "id": f"{suit}-{number:02d}",
                    "name": f"{rank} of {suit.capitalize()}",
                    "arcana": "minor",
                    "suit": suit,
                    "rank": rank,
                    "number": number,
                    "element": element,
                    "base_power": power,
                    "upright_meaning": up,
                    "reversed_meaning": rev,
                    "sports_upright": sports_up,
                    "sports_reversed": sports_rev,
                }
            )
        suits[suit] = cards
    return suits


def main() -> None:
    deck = {
        "meta": {
            "deck_size": 78,
            "systems": ["Rider-Waite"],
            "elements": {
                "Fire": "Attack",
                "Water": "Midfield / flow",
                "Earth": "Defence",
                "Air": "Strategy / tactics",
            },
        },
        "major_arcana": _build_major(),
        "minor_arcana": _build_minor(),
    }
    with open(DECK_PATH, "w", encoding="utf-8") as handle:
        json.dump(deck, handle, indent=2, ensure_ascii=False)
    total = len(deck["major_arcana"]) + sum(
        len(cards) for cards in deck["minor_arcana"].values()
    )
    print(f"Wrote {DECK_PATH} with {total} cards")


if __name__ == "__main__":
    main()