from collections.abc import Mapping
from typing import Final

from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.presentation.fixture import Fixture
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.setting import Setting
from cardwork.states.award import Award
from cardwork.states.state import GameState
from cardwork.zones.zone import ZoneId
from cardwork.zones.zones import HANDS, hand_of
from tests.games.demo import TRAYS, tray_of

TITLE: Final[str] = "Sealed round"
DRAW: Final[ZoneId] = "draw"
DISCARD: Final[ZoneId] = "discard"

TABLE: Final[tuple[Fixture, ...]] = (
    Fixture.heap(DRAW, "Draw"),
    Fixture.heap(DISCARD, "Discard"),
)

SEATED: Final[tuple[Setting, ...]] = (
    Setting.hand(HANDS, "Hand", mine="Your hand", tally="Hand"),
    Setting.sealed(TRAYS, "Sealed"),
)

READOUTS: Final[tuple[Readout, ...]] = (
    Readout.of(GameState, "points", "Points", scope=Scope.SEAT),
    Readout.of(GameState, "phase", "Phase", scope=Scope.TABLE),
)

PHASES: Final[Mapping[str, str]] = {
    "deal": "Dealing",
    "play": "Seal a card",
    "score": "Round scored",
}

INTERLUDES: Final[Mapping[str, Interlude]] = {"score": Interlude.ROUND}

AWARD: Final[Award] = Award.HIGHEST


def gestures_of(seat: int) -> tuple[Gesture, ...]:
    """The commitment a seat seals and the take-back lifting it out again, which run in either direction."""
    return (
        Gesture(
            kind=ActionKind.PLAY,
            group=None,
            picked=hand_of(seat),
            commit=Commit.ZONE,
            target=tray_of(seat),
            caption="Seal this card",
        ),
        Gesture(
            kind=ActionKind.TAKE,
            group=None,
            picked=tray_of(seat),
            commit=Commit.ZONE,
            target=hand_of(seat),
            caption="Take back what you sealed",
        ),
    )


SEALED_SCENE: Final[Scene] = Scene(
    title=TITLE,
    table=TABLE,
    seated=SEATED,
    gestures=gestures_of,
    readouts=READOUTS,
    phases=PHASES,
    interludes=INTERLUDES,
    award=AWARD,
)
