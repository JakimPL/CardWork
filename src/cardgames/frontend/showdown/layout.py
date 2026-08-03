from collections.abc import Mapping
from typing import Final

from cardgames.backend.showdown.state import ShowdownPhase, ShowdownState
from cardgames.backend.showdown.zones import DISCARD, HOLDINGS, STOCK, blind_of, hand_of, tray_of, zone_of
from cardwork.moves.kind import ActionKind
from cardwork.presentation import presets
from cardwork.presentation.commit import Commit
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.readout import Readout
from cardwork.presentation.region import Region
from cardwork.presentation.scene import Scene
from cardwork.presentation.scope import Scope
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.presentation.tally import Tally
from cardwork.rounds.state import MatchPhase

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


def slots_of(seat: int) -> tuple[Slot, ...]:
    """The two holdings a seat commits from, and the tray a commitment lies sealed in.

    The hand fans out, since a seat reads those five and picks by what they are. The blind lies in a row of
    whole cards, since a seat reads none of them and picks by where one lies, which the projection serves at
    its true position for exactly that. The tray holds the one card of the turn.
    """
    return (
        presets.hand(hand_of(seat), "Your hand", place=HELD),
        Slot(
            zone=blind_of(seat),
            label="Your blind",
            region=Region.SEAT,
            spread=Spread.ROW,
            place=BLIND,
            counted=False,
        ),
        Slot(
            zone=tray_of(seat),
            label="Sealed",
            region=Region.SEAT,
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
            group=holding,
            picked=zone_of(holding, seat),
            commit=Commit.ZONE,
            target=tray_of(seat),
            caption=f"Seal this card from your {holding}",
        )
        for holding in HOLDINGS
    )


def counts_of(seat: int) -> tuple[Tally, ...]:
    """What the table reads of a seat: the size of both holdings, and a tray saying whether it has committed."""
    return (
        Tally(zone=hand_of(seat), label="Hand"),
        Tally(zone=blind_of(seat), label="Blind"),
        Tally(zone=tray_of(seat), label="Sealed"),
    )


SHOWDOWN_SCENE: Final[Scene] = Scene(
    title=TITLE,
    shared=SHARED,
    held=slots_of,
    gestures=gestures_of,
    counts=counts_of,
    readouts=READOUTS,
    phases=PHASES,
)
