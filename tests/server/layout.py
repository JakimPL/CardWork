from collections.abc import Mapping
from typing import Final

from cardwork.moves.kind import ActionKind
from cardwork.presentation import presets
from cardwork.presentation.commit import Commit
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.presentation.tally import Tally
from cardwork.states.state import GameState
from cardwork.zones.zone import ZoneId

from ..games.demo import hand_of, tray_of

TITLE: Final[str] = "Sealed round"
DRAW: Final[ZoneId] = "draw"
DISCARD: Final[ZoneId] = "discard"

HELD: Final[int] = 0
SEALED: Final[int] = 1
DEALT_FROM: Final[int] = 0
LAID_ON: Final[int] = 1

SHARED: Final[tuple[Slot, ...]] = (
    presets.heap(DRAW, "Draw", place=DEALT_FROM),
    presets.heap(DISCARD, "Discard", place=LAID_ON),
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


def slots_of(seat: int) -> tuple[Slot, ...]:
    """The hand a seat seals a card from, and the tray the card sits in while the round stays open."""
    return (
        presets.hand(hand_of(seat), "Your hand", seat=seat, place=HELD),
        Slot(
            zone=tray_of(seat),
            label="Sealed",
            seat=seat,
            spread=Spread.SLOT,
            place=SEALED,
            counted=False,
        ),
    )


def seen_of(seat: int) -> tuple[Slot, ...]:
    """The same two zones as the rest of the table reads them: a holding counted, and a tray it can watch."""
    return (
        presets.holding(hand_of(seat), "Hand", seat=seat, place=HELD),
        Slot(
            zone=tray_of(seat),
            label="Sealed",
            seat=seat,
            spread=Spread.SLOT,
            place=SEALED,
            counted=False,
        ),
    )


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


def counts_of(seat: int) -> tuple[Tally, ...]:
    """What the table reads of a seat: the cards it holds, and whether it has sealed one."""
    return (
        Tally(zone=hand_of(seat), label="Hand"),
        Tally(zone=tray_of(seat), label="Sealed"),
    )


SEALED_SCENE: Final[Scene] = Scene(
    title=TITLE,
    shared=SHARED,
    held=slots_of,
    seen=seen_of,
    gestures=gestures_of,
    counts=counts_of,
    readouts=READOUTS,
    phases=PHASES,
)
