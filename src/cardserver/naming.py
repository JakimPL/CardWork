from collections.abc import Mapping

from cardserver.protocol import Presentation
from cardwork.models.base import BaseFrozen
from cardwork.presentation.layout import Layout
from cardwork.presentation.plaque import Plaque
from cardwork.presentation.tint import Tint


class Seated(BaseFrozen):
    """One seat as the table it was dealt into reads it: the name its guest took it under, and their tint.

    This is the whole of what a gathering has to say about a player, and it is what a plaque carries: who is
    there, and which of the company's tints tells them apart from the rest.
    """

    name: str
    tint: Tint


class Named:
    """A table's arrangement with the names and tints its gathering settled read onto its plaques.

    A seat is named by where it sits and plays under no tint until a host holds them for one, and a gathering is
    where a host comes to hold both: the guest who took a seat is read at it by the name they arrived under and
    the tint the company tells them apart by. Wrapping the arrangement is the whole of what that takes, since a
    plaque already states who is at a seat and every interface already draws it from there.

    Both settle as the table is dealt and stand for the match, which is what makes one wrapper enough: a layout
    answers for the match rather than for the position, so a page reads it once as it joins.
    """

    def __init__(
        self,
        presentation: Presentation,
        seated: Mapping[int, Seated],
    ) -> None:
        self._presentation = presentation
        self._seated = seated

    def layout(self, players: int, observer: int | None) -> Layout:
        """How a table of that many seats is laid out for one observer, with its seats named and tinted."""
        drawn = self._presentation.layout(players, observer)
        return drawn.model_copy(update={"plaques": tuple(self._naming(plaque) for plaque in drawn.plaques)})

    def _naming(self, plaque: Plaque) -> Plaque:
        """One plaque as its seat was taken, and as it came where the seat stands empty."""
        seated = self._seated.get(plaque.seat)
        if seated is None:
            return plaque

        return plaque.model_copy(update={"name": seated.name, "tint": seated.tint})
