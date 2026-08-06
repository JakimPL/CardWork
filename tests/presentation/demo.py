from collections.abc import Mapping
from typing import Final

from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.presentation.fixture import Fixture
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.lay import Lay
from cardwork.presentation.layout import Layout
from cardwork.presentation.making import Making
from cardwork.presentation.plaque import Plaque
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.setting import Setting
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.presentation.tally import Tally
from cardwork.states.award import Award
from cardwork.states.state import GameState
from cardwork.zones.zone import ZoneId
from cardwork.zones.zones import HANDS, hand_of

SEATS: Final[int] = 3
OWNER: Final[int] = 1
OTHER: Final[int] = 2
PILE: Final[ZoneId] = "pile"
STACK: Final[ZoneId] = "stack"
PLAYING: Final[str] = "playing"
SCORED: Final[str] = "scored"
TITLE: Final[str] = "Demonstration"
PHASES: Final[Mapping[str, str]] = {PLAYING: "Your turn", SCORED: "Round scored"}
INTERLUDES: Final[Mapping[str, Interlude]] = {SCORED: Interlude.ROUND}
AWARD: Final[Award] = Award.LOWEST


def a_hand(seat: int) -> Slot:
    """The hand one seat holds, as that seat reads it: every card of it, and no count."""
    return Slot(
        zone=hand_of(seat),
        label="Your hand",
        seat=seat,
        spread=Spread.FAN,
        place=0,
        counted=False,
    )


def a_holding(seat: int) -> Slot:
    """The same hand as the rest of the table reads it, which lies the same way and carries its size."""
    return Slot(
        zone=hand_of(seat),
        label="Hand",
        seat=seat,
        spread=Spread.FAN,
        place=0,
        counted=True,
    )


def an_exchange(seat: int) -> Gesture:
    """One seat's exchange with the pile, which picks in its hand and commits onto a zone."""
    return Gesture(
        kind=ActionKind.TAKE,
        group=PILE,
        picked=hand_of(seat),
        commit=Commit.ZONE,
        target=PILE,
        caption="Exchange with the pile",
    )


def a_pass(seat: int) -> Gesture:
    """One seat's pass to the next, which picks in its hand and commits onto a seat."""
    return Gesture(
        kind=ActionKind.GIVE,
        group=None,
        picked=hand_of(seat),
        commit=Commit.SEAT,
        target=None,
        caption="Pass to the next seat",
    )


GIVEN_UP: Final[Gesture] = Gesture(
    kind=ActionKind.PASS,
    group=None,
    picked=None,
    commit=Commit.WORD,
    target=None,
    caption="Pass",
)

HELD: Final[Slot] = a_hand(OWNER)
DEALT_FROM: Final[Slot] = Slot(
    zone=PILE,
    label="Pile",
    seat=None,
    spread=Spread.STACK,
    place=0,
    counted=True,
)
LAID_ON: Final[Slot] = Slot(
    zone=STACK,
    label="Stack",
    seat=None,
    spread=Spread.STACK,
    place=1,
    counted=False,
)
SHARED: Final[tuple[Slot, ...]] = (DEALT_FROM, LAID_ON)
AROUND: Final[tuple[Slot, ...]] = tuple(a_holding(seat) for seat in range(SEATS) if seat != OWNER)
SLOTS: Final[tuple[Slot, ...]] = (HELD,) + AROUND + SHARED

EXCHANGE: Final[Gesture] = an_exchange(OWNER)
PASS_ON: Final[Gesture] = a_pass(OWNER)
GESTURES: Final[tuple[Gesture, ...]] = (EXCHANGE, PASS_ON)

EXCHANGING: Final[Making] = Making(
    kind=ActionKind.TAKE,
    group=PILE,
    picked=HANDS,
    commit=Commit.ZONE,
    target=PILE,
    caption="Exchange with the pile",
)
PASSING: Final[Making] = Making(
    kind=ActionKind.GIVE,
    group=None,
    picked=HANDS,
    commit=Commit.SEAT,
    target=None,
    caption="Pass to the next seat",
)
MAKINGS: Final[tuple[Making, ...]] = (EXCHANGING, PASSING)


def slots_of(seat: int) -> tuple[Slot, ...]:
    """The one zone a seat holds of its own, which is the hand it plays from."""
    return (a_hand(seat),)


def gestures_of(seat: int) -> tuple[Gesture, ...]:
    """The two moves one seat makes, which between them commit onto a zone and onto a seat."""
    return (an_exchange(seat), a_pass(seat))


def counts_of(seat: int) -> tuple[Tally, ...]:
    """What the table reads of one seat's cards, which is how many it holds."""
    return (Tally(zone=hand_of(seat), label="Held"),)


PLAQUES: Final[tuple[Plaque, ...]] = tuple(
    Plaque(
        seat=seat,
        name=f"Seat {seat}",
        tint=None,
        counts=counts_of(seat),
    )
    for seat in range(SEATS)
)

STANDING: Final[Readout] = Readout.of(GameState, "points", "Points", scope=Scope.SEAT)
STAGE: Final[Readout] = Readout.of(GameState, "phase", "Phase", scope=Scope.TABLE)
READOUTS: Final[tuple[Readout, ...]] = (STANDING, STAGE)

TABLE: Final[tuple[Fixture, ...]] = (
    Fixture.heap(PILE, "Pile"),
    Fixture(zone=STACK, seen=Lay(label="Stack", spread=Spread.STACK, counted=False)),
)
SEATED: Final[tuple[Setting, ...]] = (Setting.hand(HANDS, "Hand", mine="Your hand", tally="Held"),)


def a_scene(
    table: tuple[Fixture, ...] = TABLE,
    seated: tuple[Setting, ...] = SEATED,
    gestures: tuple[Making, ...] = MAKINGS,
    readouts: tuple[Readout, ...] = READOUTS,
    phases: Mapping[str, str] = PHASES,
    interludes: Mapping[str, Interlude] = INTERLUDES,
) -> Scene:
    """The demonstration table stated once for every seat, with any part of it standing in for its own.

    A scene answers for itself as it is built, so a rule it is held to is tested by stating a scene that breaks
    that one part and leaving the rest of the table as it stands.
    """
    return Scene(
        title=TITLE,
        table=table,
        seated=seated,
        gestures=gestures,
        readouts=readouts,
        phases=phases,
        interludes=interludes,
        award=AWARD,
    )


SCENE: Final[Scene] = a_scene()


def a_layout(
    slots: tuple[Slot, ...] = SLOTS,
    gestures: tuple[Gesture, ...] = GESTURES,
    plaques: tuple[Plaque, ...] = PLAQUES,
    readouts: tuple[Readout, ...] = READOUTS,
    observer: int | None = OWNER,
    players: int = SEATS,
    interludes: Mapping[str, Interlude] = INTERLUDES,
) -> Layout:
    """The demonstration table laid out for one seat, with any part of it standing in for its own.

    The table is a hand held, the hands of the seats around it, a pile dealt from and a stack laid on, which
    between them exercise every owner a slot may name, a commit onto a zone and a commit onto a seat. `SCENE`
    states the same table for every seat at once, so a layout built by hand here and one a scene lays out are
    the same thing for the owner.
    """
    return Layout(
        title=TITLE,
        observer=observer,
        players=players,
        slots=slots,
        gestures=gestures,
        plaques=plaques,
        readouts=readouts,
        phases=PHASES,
        interludes=interludes,
        award=AWARD,
    )
