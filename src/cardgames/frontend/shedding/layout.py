from collections.abc import Mapping
from typing import Final

from cardgames.backend.shedding.rules import AWARD
from cardgames.backend.shedding.state import SheddingPhase, SheddingState
from cardgames.backend.shedding.zones import HAND, STOCK
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
from cardwork.zones.zones import DISCARD, hand_of

TITLE: Final[str] = "Shedding"

HELD: Final[int] = 0
DRAWN_FROM: Final[int] = 0
SHED_ONTO: Final[int] = 1

SHARED: Final[tuple[Slot, ...]] = (
    presets.heap(STOCK, "Stock", place=DRAWN_FROM),
    presets.heap(DISCARD, "Shed", place=SHED_ONTO),
)

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


def slots_of(seat: int) -> tuple[Slot, ...]:
    """The hand a seat sheds from, which is the zone the positions of a set address.

    A hand fans out, since a seat picks its cards by what they are and reads the rank of each one to find the
    others that go with it. It grows by the cards a turn draws, so this is the one holding in either game that
    lies at no settled size.
    """
    return (presets.hand(hand_of(seat), "Your hand", seat=seat, place=HELD),)


def seen_of(seat: int) -> tuple[Slot, ...]:
    """The same hand as the rest of the table reads it, which is how the race to shed out is followed.

    A seat down to two cards is what everybody else is playing against, so the size of a holding is the whole of
    what a hand tells the table, and it lies there to be counted at a glance.
    """
    return (presets.holding(hand_of(seat), "Hand", seat=seat, place=HELD),)


def gestures_of(seat: int) -> tuple[Gesture, ...]:
    """The two moves a turn is made of: a set laid down, and a card taken up.

    A set is picked out of the seat's own hand and sent onto the discard it goes face up on, so a selection of
    one card arms nothing until a second of that rank joins it. A draw runs the other way — the card is picked
    off the stock the whole table shares and sent onto the seat's own hand — which is the one gesture of either
    game that takes a card rather than lays one down.
    """
    return (
        Gesture(
            kind=ActionKind.DISCARD,
            group=HAND,
            picked=hand_of(seat),
            commit=Commit.ZONE,
            target=DISCARD,
            caption="Shed these cards as one rank",
        ),
        Gesture(
            kind=ActionKind.TAKE,
            group=STOCK,
            picked=STOCK,
            commit=Commit.ZONE,
            target=hand_of(seat),
            caption="Draw this card into your hand",
        ),
    )


def counts_of(seat: int) -> tuple[Tally, ...]:
    """What the table reads of a seat's cards, which is how many of them it holds."""
    return (Tally(zone=hand_of(seat), label="Cards"),)


SHEDDING_SCENE: Final[Scene] = Scene(
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
