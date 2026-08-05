from collections.abc import Mapping
from typing import Final

from cardgames.backend.passing.rules import AWARD
from cardgames.backend.passing.state import PassingPhase, PassingState
from cardgames.backend.passing.zones import PILE
from cardwork.moves.kind import ActionKind
from cardwork.presentation import presets
from cardwork.presentation.commit import Commit
from cardwork.presentation.fixture import Fixture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.making import Making
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.setting import Setting
from cardwork.rounds.state import MatchPhase
from cardwork.zones.zones import HANDS, STACK

TITLE: Final[str] = "Passing"

TABLE: Final[tuple[Fixture, ...]] = (
    Fixture.heap(PILE, "Pile"),
    Fixture.heap(STACK, "Stack"),
)

SEATED: Final[tuple[Setting, ...]] = (Setting.hand(HANDS, "Hand", mine="Your hand", tally="Cards"),)

READOUTS: Final[tuple[Readout, ...]] = (
    Readout.of(PassingState, "points", "Points", scope=Scope.SEAT),
    Readout.of(PassingState, "round_points", "This round", scope=Scope.SEAT),
    Readout.of(PassingState, "round_number", "Round", scope=Scope.TABLE),
    Readout.of(PassingState, "winner", "Won by", scope=Scope.TABLE),
)

PHASES: Final[Mapping[str, str]] = {
    PassingPhase.PASSING: "Passing",
    PassingPhase.DECIDED: "Round decided",
    MatchPhase.BETWEEN_ROUNDS: "Between rounds",
    MatchPhase.MATCH_OVER: "Match over",
}

INTERLUDES: Final[Mapping[str, Interlude]] = presets.match_interludes()


GESTURES: Final[tuple[Making, ...]] = (
    Making(
        kind=ActionKind.TAKE,
        group=PILE,
        picked=HANDS,
        commit=Commit.ZONE,
        target=PILE,
        caption="Exchange this card for the top of the pile",
    ),
    Making(
        kind=ActionKind.GIVE,
        group=None,
        picked=HANDS,
        commit=Commit.SEAT,
        target=None,
        caption="Pass this card to the next seat",
    ),
)

PASSING_SCENE: Final[Scene] = Scene(
    title=TITLE,
    table=TABLE,
    seated=SEATED,
    gestures=GESTURES,
    readouts=READOUTS,
    phases=PHASES,
    interludes=INTERLUDES,
    award=AWARD,
)
