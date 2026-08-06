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
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.lay import Lay
from cardwork.presentation.making import Making
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.setting import Setting
from cardwork.presentation.spread import Spread
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

READOUTS: Final[tuple[Readout, ...]] = presets.match_readouts(ShowdownState) + (
    Readout.of(ShowdownState, "rounds", "Rounds", scope=Scope.TABLE),
    Readout.of(ShowdownState, "turn_number", "Turn", scope=Scope.TABLE),
)

PHASES: Final[Mapping[str, str]] = {
    ShowdownPhase.COMMITTING: "Commit a card",
    **presets.match_phases(),
}

INTERLUDES: Final[Mapping[str, Interlude]] = presets.match_interludes()


GESTURES: Final[tuple[Making, ...]] = tuple(
    Making(
        kind=ActionKind.PLAY,
        group=holding,
        picked=holding,
        commit=Commit.ZONE,
        target=TRAYS,
        caption=f"Seal this card from your {holding.name}",
    )
    for holding in HOLDINGS
)

SHOWDOWN_SCENE: Final[Scene] = Scene(
    title=TITLE,
    table=TABLE,
    seated=SEATED,
    gestures=GESTURES,
    readouts=READOUTS,
    phases=PHASES,
    interludes=INTERLUDES,
    award=AWARD,
)
