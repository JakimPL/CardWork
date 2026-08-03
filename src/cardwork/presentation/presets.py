from cardwork.presentation.region import Region
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.zones.zone import ZoneId


def hand(zone: ZoneId, label: str, *, place: int) -> Slot:
    """A holding the observer reads and picks from, overlapped so every card of it stays legible.

    A hand lies in the observer's own region and shows its cards in place of a count, since a seat reading
    its own holding counts it by looking.
    """
    return Slot(
        zone=zone,
        label=label,
        region=Region.SEAT,
        spread=Spread.FAN,
        place=place,
        counted=False,
    )


def heap(zone: ZoneId, label: str, *, place: int) -> Slot:
    """A stack on the shared table, read by the card lying on top of it and by how many lie beneath.

    A heap counts, since the size is what a stack of cards has to say for itself at either face: how much
    stock is left to come is what a seat weighs, and how much has been laid down is what it has watched.
    """
    return Slot(
        zone=zone,
        label=label,
        region=Region.TABLE,
        spread=Spread.STACK,
        place=place,
        counted=True,
    )
