from cardwork.models.base import BaseFrozen
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.zones.zone import ZoneId


class Lay(BaseFrozen):
    """The lay of a zone from one side of the table: what it is called, how its cards lie, and whether it counts.

    A zone is read from as many sides as it has readers. The seat holding a hand reads the cards in it, and the
    rest of the table reads the backs of them and how many there are, so the same zone carries one word and one
    arrangement at the seat it belongs to and another across the table. A zone the seats share carries one lay,
    since everybody reads it alike.

    `counted` shows how many cards lie there, which is what a zone says for itself where its cards are not to be
    counted by looking: a heap read by its top card, a holding drawn as backs. A single place holds one card or
    stands empty, which the drawing of it says.
    """

    label: str
    spread: Spread
    counted: bool

    def slot(self, zone: ZoneId, *, seat: int | None, place: int) -> Slot:
        """This lay given to one zone, which is the slot an observer reads that zone through.

        Args:
            zone: the zone lying this way, concrete for the seat it is read at.
            seat: the seat it belongs to, and None for a zone of the table.
            place: where it stands among the zones of that owner.
        """
        return Slot(
            zone=zone,
            label=self.label,
            seat=seat,
            spread=self.spread,
            place=place,
            counted=self.counted,
        )
