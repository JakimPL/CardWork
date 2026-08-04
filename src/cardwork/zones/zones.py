from cardwork.zones.presets import HAND, HIDDEN
from cardwork.zones.zone import Zone, Zones, hand_of

DISCARD = "discard"
STACK = "stack"


def hands(players: int) -> Zones:
    """The zone ids of the hands each seat holds, which is what the rules read against."""
    return {
        hand_of(seat): Zone(
            id=hand_of(seat),
            owner=seat,
            visibility=HAND,
        )
        for seat in range(players)
    }


def discard() -> Zones:
    """The zone id of the discard pile, which is what the rules read against."""
    return {DISCARD: Zone(id=DISCARD, visibility=HIDDEN)}


def stack() -> Zones:
    """The zone id of the stack pile, which is what the rules read against."""
    return {STACK: Zone(id=STACK, visibility=HAND)}
