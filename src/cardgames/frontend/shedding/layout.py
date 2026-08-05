from collections.abc import Mapping
from typing import Final

from cardgames.backend.shedding.rules import AWARD
from cardgames.backend.shedding.state import SheddingPhase, SheddingState
from cardgames.backend.shedding.zones import STOCK
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


GESTURES: Final[tuple[Making, ...]] = (
    Making(
        kind=ActionKind.DISCARD,
        group=HANDS,
        picked=HANDS,
        commit=Commit.ZONE,
        target=DISCARD,
        caption="Shed these cards as one rank",
    ),
    Making(
        kind=ActionKind.TAKE,
        group=STOCK,
        picked=STOCK,
        commit=Commit.ZONE,
        target=HANDS,
        caption="Draw this card into your hand",
    ),
)

SHEDDING_SCENE: Final[Scene] = Scene(
    title=TITLE,
    table=TABLE,
    seated=SEATED,
    gestures=GESTURES,
    readouts=READOUTS,
    phases=PHASES,
    interludes=INTERLUDES,
    award=AWARD,
)
