from collections.abc import Mapping

from cardwork.presentation.interlude import Interlude
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.rounds.state import MatchPhase
from cardwork.zones.zone import ZoneId


def match_interludes() -> Mapping[str, Interlude]:
    """The two phases a match played in rounds pauses at, which is where `MatchPhase` leaves the table at rest.

    A round closed stands between rounds until the next is dealt, and a match decided stands over for good, so
    the two members of `MatchPhase` are exactly the two pauses a player reads a round game through. A game
    pausing somewhere of its own — a trick taken, a hand revealed — names that phase beside these.
    """
    return {
        MatchPhase.BETWEEN_ROUNDS: Interlude.ROUND,
        MatchPhase.MATCH_OVER: Interlude.MATCH,
    }


def hand(zone: ZoneId, label: str, *, seat: int, place: int) -> Slot:
    """A holding the seat reading the table picks from, overlapped so every card of it stays legible.

    A hand shows its cards in place of a count, since a seat reading its own holding counts it by looking.
    """
    return Slot(
        zone=zone,
        label=label,
        seat=seat,
        spread=Spread.FAN,
        place=place,
        counted=False,
    )


def holding(zone: ZoneId, label: str, *, seat: int, place: int) -> Slot:
    """The same holding as the rest of the table reads it, lying the same way and carrying its size.

    What a seat's cards say to everybody else is how many of them there are, so a holding drawn across the
    table counts itself beside the backs standing for the cards.
    """
    return Slot(
        zone=zone,
        label=label,
        seat=seat,
        spread=Spread.FAN,
        place=place,
        counted=True,
    )


def heap(zone: ZoneId, label: str, *, place: int) -> Slot:
    """A stack the seats share, read by the card lying on top of it and by how many lie beneath.

    A heap counts, since the size is what a stack of cards has to say for itself at either face: how much
    stock is left to come is what a seat weighs, and how much has been laid down is what it has watched.
    """
    return Slot(
        zone=zone,
        label=label,
        seat=None,
        spread=Spread.STACK,
        place=place,
        counted=True,
    )
