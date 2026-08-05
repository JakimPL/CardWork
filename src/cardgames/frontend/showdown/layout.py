from collections.abc import Mapping
from typing import Final

from cardgames.backend.showdown.rules import AWARD
from cardgames.backend.showdown.state import ShowdownPhase, ShowdownState
from cardgames.backend.showdown.zones import (
    BLINDS,
    HOLDINGS,
    STOCK,
    TRAYS,
)
from cardwork.moves.kind import ActionKind
from cardwork.presentation import presets
from cardwork.presentation.commit import Commit
from cardwork.presentation.fixture import Fixture
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.lay import Lay
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.setting import Setting
from cardwork.presentation.spread import Spread
from cardwork.rounds.state import MatchPhase
from cardwork.zones.zones import DISCARD, HANDS

TITLE: Final[str] = "Showdown"

TABLE: Final[tuple[Fixture, ...]] = (
    Fixture.heap(STOCK, "Stock"),
    Fixture.heap(DISCARD, "Revealed"),
)

SEATED: Final[tuple[Setting, ...]] = (
    Setting.hand(HANDS, "Hand", mine="Your hand", tally="Hand"),
    Setting(
        family=BLINDS,
        held=Lay(label="Your blind", spread=Spread.ROW, counted=False),
        seen=Lay(label="Blind", spread=Spread.STACK, counted=True),
        tally="Blind",
    ),
    Setting.sealed(TRAYS, "Sealed"),
)

READOUTS: Final[tuple[Readout, ...]] = (
    Readout.of(ShowdownState, "points", "Points", scope=Scope.SEAT),
    Readout.of(ShowdownState, "round_points", "This round", scope=Scope.SEAT),
    Readout.of(ShowdownState, "round_number", "Round", scope=Scope.TABLE),
    Readout.of(ShowdownState, "rounds", "Rounds", scope=Scope.TABLE),
    Readout.of(ShowdownState, "turn_number", "Turn", scope=Scope.TABLE),
)

PHASES: Final[Mapping[str, str]] = {
    ShowdownPhase.COMMITTING: "Commit a card",
    MatchPhase.BETWEEN_ROUNDS: "Between rounds",
    MatchPhase.MATCH_OVER: "Match over",
}

INTERLUDES: Final[Mapping[str, Interlude]] = presets.match_interludes()


def gestures_of(seat: int) -> tuple[Gesture, ...]:
    """One gesture per holding a card is committed from, each sealing it into the seat's own tray.

    A commitment names its holding and a position within it, so the group of the gesture is the word the
    intent carries and the zone it picks in is that holding.
    """
    return tuple(
        Gesture(
            kind=ActionKind.PLAY,
            group=holding.name,
            picked=holding.of(seat),
            commit=Commit.ZONE,
            target=TRAYS.of(seat),
            caption=f"Seal this card from your {holding.name}",
        )
        for holding in HOLDINGS
    )


SHOWDOWN_SCENE: Final[Scene] = Scene(
    title=TITLE,
    table=TABLE,
    seated=SEATED,
    gestures=gestures_of,
    readouts=READOUTS,
    phases=PHASES,
    interludes=INTERLUDES,
    award=AWARD,
)
