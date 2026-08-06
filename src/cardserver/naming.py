from collections.abc import Mapping

from cardserver.protocol import Presentation
from cardwork.presentation.layout import Layout
from cardwork.presentation.plaque import Plaque


class Named:
    """A table's arrangement with the names its gathering settled read onto its plaques.

    A seat is named by where it sits until a host holds a name for one, and a gathering is where a host comes
    to hold them: the guest who took a seat is read at it by the name they arrived under. Wrapping the
    arrangement is the whole of what that takes, since a plaque already states who is at a seat and every
    interface already draws it from there.

    Names settle as the table is dealt and stand for the match, which is what makes one wrapper enough: a
    layout answers for the match rather than for the position, so a page reads it once as it joins.
    """

    def __init__(
        self,
        presentation: Presentation,
        names: Mapping[int, str],
    ) -> None:
        self._presentation = presentation
        self._names = names

    def layout(self, players: int, observer: int | None) -> Layout:
        """How a table of that many seats is laid out for one observer, with its seats named."""
        drawn = self._presentation.layout(players, observer)
        return drawn.model_copy(update={"plaques": tuple(self._naming(plaque) for plaque in drawn.plaques)})

    def _naming(self, plaque: Plaque) -> Plaque:
        """One plaque under the name its seat was taken by, and as it came where the seat stands empty."""
        name = self._names.get(plaque.seat)
        if name is None:
            return plaque

        return plaque.model_copy(update={"name": name})
