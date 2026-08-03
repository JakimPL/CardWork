from cardwork.models.base import BaseFrozen
from cardwork.zones.zone import ZoneId


class Tally(BaseFrozen):
    """A count of one zone shown on a plaque, under the word the game calls that zone by.

    A count is what a zone belonging to another seat says about itself: the cards are that seat's to read, and
    how many of them there are is the table's to know. So the zones a layout lays out as slots and the zones
    it tallies on a plaque divide by whose they are.
    """

    zone: ZoneId
    label: str
