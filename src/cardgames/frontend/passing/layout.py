from collections.abc import Mapping
from typing import Final

from cardgames.backend.passing.rules import AWARD
from cardgames.backend.passing.state import PassingPhase, PassingState
from cardgames.backend.passing.zones import PILE
from cardwork.moves.kind import ActionKind
from cardwork.presentation import presets
from cardwork.presentation.commit import Commit
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.slot import Slot
from cardwork.presentation.tally import Tally
from cardwork.rounds.state import MatchPhase
from cardwork.zones.zone import hand_of
from cardwork.zones.zones import STACK

TITLE: Final[str] = "Passing"

HELD: Final[int] = 0
DEALT_FROM: Final[int] = 0
LAID_ON: Final[int] = 1

SHARED: Final[tuple[Slot, ...]] = (
    presets.heap(PILE, "Pile", place=DEALT_FROM),
    presets.heap(STACK, "Stack", place=LAID_ON),
)

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


def slots_of(seat: int) -> tuple[Slot, ...]:
    """The hand a seat plays from, which is the zone either move of a turn picks its card in."""
    return (presets.hand(hand_of(seat), "Your hand", seat=seat, place=HELD),)


def seen_of(seat: int) -> tuple[Slot, ...]:
    """The same hand as the rest of the table reads it, which is the backs of its cards and how many.

    A pass is committed onto the seat it goes to, so the cards of that seat are what a player points at to send
    one, and the hand lies on the table for exactly that.
    """
    return (presets.holding(hand_of(seat), "Hand", seat=seat, place=HELD),)


def gestures_of(seat: int) -> tuple[Gesture, ...]:
    """The two moves a turn is made of, as the seat holding it makes them.

    Both pick a card out of the seat's own hand, which is what the indices of either intent address. The
    exchange is sent onto the pile it trades with, and the pass onto the seat the move names, so a card is
    committed by pointing at where it goes.
    """
    return (
        Gesture(
            kind=ActionKind.TAKE,
            group=PILE,
            picked=hand_of(seat),
            commit=Commit.ZONE,
            target=PILE,
            caption="Exchange this card for the top of the pile",
        ),
        Gesture(
            kind=ActionKind.GIVE,
            group=None,
            picked=hand_of(seat),
            commit=Commit.SEAT,
            target=None,
            caption="Pass this card to the next seat",
        ),
    )


def counts_of(seat: int) -> tuple[Tally, ...]:
    """What the table reads of a seat's cards, which is how many of them it holds."""
    return (Tally(zone=hand_of(seat), label="Cards"),)


PASSING_SCENE: Final[Scene] = Scene(
    title=TITLE,
    shared=SHARED,
    held=slots_of,
    seen=seen_of,
    gestures=gestures_of,
    counts=counts_of,
    readouts=READOUTS,
    phases=PHASES,
    interludes=INTERLUDES,
    award=AWARD,
)
