from collections.abc import Mapping
from typing import Final

from cardgames.backend.climbing.rules import AWARD
from cardgames.backend.climbing.state import ClimbingPhase, ClimbingState
from cardwork.moves.kind import ActionKind
from cardwork.presentation import presets
from cardwork.presentation.commit import Commit
from cardwork.presentation.fixture import Fixture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.lay import Lay
from cardwork.presentation.making import Making
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.setting import Setting
from cardwork.presentation.spread import Spread
from cardwork.zones.zones import DISCARD, HANDS, STACK

TITLE: Final[str] = "Climbing"

TABLE: Final[tuple[Fixture, ...]] = (
    Fixture(zone=STACK, seen=Lay(label="Played", spread=Spread.FAN, counted=True)),
    Fixture.heap(DISCARD, "Aside"),
)

SEATED: Final[tuple[Setting, ...]] = (Setting.hand(HANDS, "Hand", mine="Your hand", tally="Cards"),)

READOUTS: Final[tuple[Readout, ...]] = presets.match_readouts(ClimbingState) + (
    Readout.of(ClimbingState, "rounds", "Rounds", scope=Scope.TABLE),
    Readout.of(ClimbingState, "winner", "Out first", scope=Scope.TABLE),
)

PHASES: Final[Mapping[str, str]] = {
    ClimbingPhase.LEAD: "Put down any combination",
    ClimbingPhase.FOLLOW: "Climb over the combination on the table, or pass",
    ClimbingPhase.DECIDED: "Round decided",
    **presets.match_phases(),
}

INTERLUDES: Final[Mapping[str, Interlude]] = presets.match_interludes()


GESTURES: Final[tuple[Making, ...]] = (
    Making(
        kind=ActionKind.PLAY,
        group=HANDS,
        picked=HANDS,
        commit=Commit.ZONE,
        target=STACK,
        caption="Play these cards as one combination",
    ),
    Making(
        kind=ActionKind.PASS,
        group=None,
        picked=None,
        commit=Commit.WORD,
        target=None,
        caption="Give your turn up",
    ),
)

CLIMBING_SCENE: Final[Scene] = Scene(
    title=TITLE,
    table=TABLE,
    seated=SEATED,
    gestures=GESTURES,
    readouts=READOUTS,
    phases=PHASES,
    interludes=INTERLUDES,
    award=AWARD,
)
