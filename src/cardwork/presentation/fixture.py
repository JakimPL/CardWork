from typing import Self

from cardwork.models.base import BaseFrozen
from cardwork.presentation.lay import Lay
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.zones.zone import ZoneId


class Fixture(BaseFrozen):
    """A zone of the table, which belongs to no seat and every observer reads the same way.

    The pile a round is dealt from, the stack it is laid on, the discard it sheds onto: each stands in the
    middle of the table and says the same thing to everybody, so one lay is the whole of what a game states
    about it.
    """

    zone: ZoneId
    seen: Lay

    def slot(self, place: int) -> Slot:
        """This zone as every observer reads it, standing where the scene states it among the table's own.

        Args:
            place: where it stands among the zones of the table.
        """
        return self.seen.slot(self.zone, seat=None, place=place)

    @classmethod
    def heap(cls, zone: ZoneId, label: str) -> Self:
        """A stack the seats share, read by the card lying on top of it and by how many lie beneath.

        A heap counts, since the size is what a stack of cards has to say for itself at either face: how much
        stock is left to come is what a seat weighs, and how much has been laid down is what it has watched.
        """
        return cls(
            zone=zone,
            seen=Lay(
                label=label,
                spread=Spread.STACK,
                counted=True,
            ),
        )
