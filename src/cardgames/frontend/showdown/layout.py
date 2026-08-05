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
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.presentation.tally import Tally
from cardwork.rounds.state import MatchPhase
from cardwork.zones.zones import DISCARD, HANDS

TITLE: Final[str] = "Showdown"

HELD: Final[int] = 0
BLIND: Final[int] = 1
SEALED: Final[int] = 2
DEALT_FROM: Final[int] = 0
REVEALED: Final[int] = 1

SHARED: Final[tuple[Slot, ...]] = (
    presets.heap(STOCK, "Stock", place=DEALT_FROM),
    presets.heap(DISCARD, "Revealed", place=REVEALED),
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


def slots_of(seat: int) -> tuple[Slot, ...]:
    """The two holdings a seat commits from, and the tray a commitment lies sealed in.

    The hand fans out, since a seat reads those five and picks by what they are. The blind lies in a row of
    whole cards, since a seat reads none of them and picks by where one lies, which the projection serves at
    its true position for exactly that. The tray holds the one card of the turn.
    """
    return (
        presets.hand(HANDS.of(seat), "Your hand", seat=seat, place=HELD),
        Slot(
            zone=BLINDS.of(seat),
            label="Your blind",
            seat=seat,
            spread=Spread.ROW,
            place=BLIND,
            counted=False,
        ),
        Slot(
            zone=TRAYS.of(seat),
            label="Sealed",
            seat=seat,
            spread=Spread.SLOT,
            place=SEALED,
            counted=False,
        ),
    )


def seen_of(seat: int) -> tuple[Slot, ...]:
    """The three zones of a seat as the rest of the table reads them: a holding, a blind, and a tray.

    A blind nobody reads says one thing to the table, which is how many cards are still to come out of it, so it
    lies across the table as a heap under its size where the seat holding it reads a row of places to pick from.
    The tray shows the card sealed there once the round opens it, which is what a showdown comes to.
    """
    return (
        presets.holding(HANDS.of(seat), "Hand", seat=seat, place=HELD),
        Slot(
            zone=BLINDS.of(seat),
            label="Blind",
            seat=seat,
            spread=Spread.STACK,
            place=BLIND,
            counted=True,
        ),
        Slot(
            zone=TRAYS.of(seat),
            label="Sealed",
            seat=seat,
            spread=Spread.SLOT,
            place=SEALED,
            counted=False,
        ),
    )


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


def counts_of(seat: int) -> tuple[Tally, ...]:
    """What the table reads of a seat: the size of both holdings, and a tray saying whether it has committed."""
    return (
        Tally(zone=HANDS.of(seat), label="Hand"),
        Tally(zone=BLINDS.of(seat), label="Blind"),
        Tally(zone=TRAYS.of(seat), label="Sealed"),
    )


SHOWDOWN_SCENE: Final[Scene] = Scene(
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
