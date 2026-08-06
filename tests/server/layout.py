from collections.abc import Mapping
from typing import Final

from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.presentation.fixture import Fixture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.making import Making
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.setting import Setting
from cardwork.states.award import Award
from cardwork.states.state import GameState
from cardwork.zones.zone import ZoneId
from cardwork.zones.zones import HANDS
from tests.games.demo import TRAYS

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


GESTURES: Final[tuple[Making, ...]] = (
    Making(
        kind=ActionKind.PLAY,
        group=None,
        picked=HANDS,
        commit=Commit.ZONE,
        target=TRAYS,
        caption="Seal this card",
    ),
    Making(
        kind=ActionKind.TAKE,
        group=None,
        picked=TRAYS,
        commit=Commit.ZONE,
        target=HANDS,
        caption="Take back what you sealed",
    ),
)

SEALED_SCENE: Final[Scene] = Scene(
    title=TITLE,
    table=TABLE,
    seated=SEATED,
    gestures=GESTURES,
    readouts=READOUTS,
    phases=PHASES,
    interludes=INTERLUDES,
    award=AWARD,
)
