from collections.abc import Mapping

from cardserver.naming.seated import Seated
from cardserver.protocols.presentation import Presentation
from cardwork.presentation.layout import Layout
from cardwork.presentation.plaque import Plaque


class Named:
    """A table's arrangement with the names and tints its gathering settled read onto its plaques.

    A seat is named by where it sits and plays under no tint until a host holds them for one, and a gathering is
    where a host comes to hold both: the guest who took a seat is read at it by the name they arrived under and
    the tint the company tells them apart by. Wrapping the arrangement is the whole of what that takes, since a
    plaque already states who is at a seat and every interface already draws it from there.

    The company settles one thing more the arrangement carries: whether the table lights the cards a seat may
    play. It is no part of the rules, so it rides the layout beside the names rather than reaching the game, and
    an interface reads it once as it joins the way it reads everything else the match settled.

    All of it settles as the table is dealt and stands for the match, which is what makes one wrapper enough: a
    layout answers for the match rather than for the position, so a page reads it once as it joins.
    """

    def __init__(
        self,
        presentation: Presentation,
        seated: Mapping[int, Seated],
        *,
        cues: bool = True,
    ) -> None:
        self._presentation = presentation
        self._seated = seated
        self._cues = cues

    def layout(self, players: int, observer: int | None) -> Layout:
        """How a table of that many seats is laid out for one observer, named, tinted, and lit as the company set."""
        drawn = self._presentation.layout(players, observer)
        return drawn.model_copy(
            update={
                "plaques": tuple(self._naming(plaque) for plaque in drawn.plaques),
                "cues": self._cues,
            }
        )

    def _naming(self, plaque: Plaque) -> Plaque:
        """One plaque as its seat was taken, and as it came where the seat stands empty."""
        seated = self._seated.get(plaque.seat)
        if seated is None:
            return plaque

        return plaque.model_copy(update={"name": seated.name, "tint": seated.tint})
