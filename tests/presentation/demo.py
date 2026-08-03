from typing import Final

from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.layout import Layout
from cardwork.presentation.plaque import Plaque
from cardwork.presentation.readout import Readout
from cardwork.presentation.region import Region
from cardwork.presentation.scope import Scope
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.presentation.tally import Tally
from cardwork.states.state import GameState
from cardwork.zones.zone import ZoneId

SEATS: Final[int] = 3
OWNER: Final[int] = 1
OTHER: Final[int] = 2
PILE: Final[ZoneId] = "pile"
STACK: Final[ZoneId] = "stack"
PLAYING: Final[str] = "playing"


def hand_of(seat: int) -> ZoneId:
    return f"hand:{seat}"


HELD: Final[Slot] = Slot(
    zone=hand_of(OWNER),
    label="Your hand",
    region=Region.SEAT,
    spread=Spread.FAN,
    place=0,
    counted=False,
)
DEALT_FROM: Final[Slot] = Slot(
    zone=PILE,
    label="Pile",
    region=Region.TABLE,
    spread=Spread.STACK,
    place=0,
    counted=True,
)
LAID_ON: Final[Slot] = Slot(
    zone=STACK,
    label="Stack",
    region=Region.TABLE,
    spread=Spread.STACK,
    place=1,
    counted=False,
)
SLOTS: Final[tuple[Slot, ...]] = (HELD, DEALT_FROM, LAID_ON)

EXCHANGE: Final[Gesture] = Gesture(
    kind=ActionKind.TAKE,
    group=PILE,
    picked=hand_of(OWNER),
    commit=Commit.ZONE,
    target=PILE,
    caption="Exchange with the pile",
)
PASS_ON: Final[Gesture] = Gesture(
    kind=ActionKind.GIVE,
    group=None,
    picked=hand_of(OWNER),
    commit=Commit.SEAT,
    target=None,
    caption="Pass to the next seat",
)
GESTURES: Final[tuple[Gesture, ...]] = (EXCHANGE, PASS_ON)

PLAQUES: Final[tuple[Plaque, ...]] = tuple(
    Plaque(
        seat=seat,
        name=f"Seat {seat}",
        counts=(Tally(zone=hand_of(seat), label="Held"),),
    )
    for seat in range(SEATS)
)

STANDING: Final[Readout] = Readout.of(GameState, "points", "Points", scope=Scope.SEAT)
STAGE: Final[Readout] = Readout.of(GameState, "phase", "Phase", scope=Scope.TABLE)
READOUTS: Final[tuple[Readout, ...]] = (STANDING, STAGE)


def a_layout(
    slots: tuple[Slot, ...] = SLOTS,
    gestures: tuple[Gesture, ...] = GESTURES,
    plaques: tuple[Plaque, ...] = PLAQUES,
    readouts: tuple[Readout, ...] = READOUTS,
    observer: int | None = OWNER,
    players: int = SEATS,
) -> Layout:
    """The demonstration table laid out for one seat, with any part of it standing in for its own.

    The table is a hand held, a pile dealt from and a stack laid on, which between them exercise both
    regions, a commit onto a zone and a commit onto a seat.
    """
    return Layout(
        title="Demonstration",
        observer=observer,
        players=players,
        slots=slots,
        gestures=gestures,
        plaques=plaques,
        readouts=readouts,
        phases={PLAYING: "Your turn"},
    )
