from typing import Final

from cardwork.zones.family import Family
from cardwork.zones.presets import HAND, PILE
from cardwork.zones.zone import Zone, ZoneId, Zones

DISCARD = "discard"
STACK = "stack"

HANDS: Final[Family] = Family(name="hand", ordered=False, visibility=HAND)


def hand_of(seat: int) -> ZoneId:
    """The zone id of the hand one seat holds, which is what the rules read against."""
    return HANDS.of(seat)


def hands(players: int) -> Zones:
    """The hand each seat holds, filed under the id it is named by.

    A hand holds the cards of one seat under an arrangement that seat chooses, since the rules read the cards a
    seat has rather than the run it keeps them in. So a hand is the zone its owner sorts as it pleases, and
    `HANDS.name` is the word a client names it by.
    """
    return HANDS.zones(players)


def discard() -> Zones:
    """The zone id of the pile cards are laid onto, which lies under the policy reading a card the moment it turns.

    A discard belongs to the table rather than to a seat, so the face a card lies at settles who reads it: what
    is laid there face up is read by everybody, and what lies face down there stays unknown to all. The run it
    lies in is the record of the round, the card on top being the one the rules read, so the table keeps it.
    """
    return {DISCARD: Zone(id=DISCARD, visibility=PILE, ordered=True)}


def stack() -> Zones:
    """The zone id of the pile cards are given up onto, which lies under the same policy a discard does.

    A stack belongs to the table, so what a seat gives up onto it face up is read by the whole table, and the
    run it lies in stands as the order the seats gave those cards up in.
    """
    return {STACK: Zone(id=STACK, visibility=PILE, ordered=True)}
