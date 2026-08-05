from collections.abc import Mapping
from typing import Final

from cardgames.backend.shedding.rules import AWARD
from cardgames.backend.shedding.state import SheddingPhase, SheddingState
from cardgames.backend.shedding.zones import STOCK
from cardwork.moves.kind import ActionKind
from cardwork.presentation import presets
from cardwork.presentation.commit import Commit
from cardwork.presentation.fixture import Fixture
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.setting import Setting
from cardwork.rounds.state import MatchPhase
from cardwork.zones.zones import DISCARD, HANDS

TITLE: Final[str] = "Shedding"

TABLE: Final[tuple[Fixture, ...]] = (
    Fixture.heap(STOCK, "Stock"),
    Fixture.heap(DISCARD, "Shed"),
)

SEATED: Final[tuple[Setting, ...]] = (Setting.hand(HANDS, "Hand", mine="Your hand", tally="Cards"),)

READOUTS: Final[tuple[Readout, ...]] = (
    Readout.of(SheddingState, "points", "Points", scope=Scope.SEAT),
    Readout.of(SheddingState, "round_points", "This round", scope=Scope.SEAT),
    Readout.of(SheddingState, "round_number", "Round", scope=Scope.TABLE),
    Readout.of(SheddingState, "rounds", "Rounds", scope=Scope.TABLE),
    Readout.of(SheddingState, "winner", "Out first", scope=Scope.TABLE),
)

PHASES: Final[Mapping[str, str]] = {
    SheddingPhase.SHEDDING: "Shed two or more of one rank",
    SheddingPhase.DECIDED: "Round decided",
    MatchPhase.BETWEEN_ROUNDS: "Between rounds",
    MatchPhase.MATCH_OVER: "Match over",
}

INTERLUDES: Final[Mapping[str, Interlude]] = presets.match_interludes()


def gestures_of(seat: int) -> tuple[Gesture, ...]:
    """The two moves a turn is made of: a set laid down, and a card taken up.

    A set is picked out of the seat's own hand and sent onto the discard it goes face up on, so a selection of
    one card arms nothing until a second of that rank joins it. A draw runs the other way — the card is picked
    off the stock the whole table shares and sent onto the seat's own hand — which is the one gesture of either
    game that takes a card rather than lays one down.
    """
    return (
        Gesture(
            kind=ActionKind.DISCARD,
            group=HANDS.name,
            picked=HANDS.of(seat),
            commit=Commit.ZONE,
            target=DISCARD,
            caption="Shed these cards as one rank",
        ),
        Gesture(
            kind=ActionKind.TAKE,
            group=STOCK,
            picked=STOCK,
            commit=Commit.ZONE,
            target=HANDS.of(seat),
            caption="Draw this card into your hand",
        ),
    )


SHEDDING_SCENE: Final[Scene] = Scene(
    title=TITLE,
    table=TABLE,
    seated=SEATED,
    gestures=gestures_of,
    readouts=READOUTS,
    phases=PHASES,
    interludes=INTERLUDES,
    award=AWARD,
)
