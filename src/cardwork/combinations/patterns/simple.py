from abc import ABC
from typing import Annotated, Final

from pydantic import Field

from cardwork.combinations.pattern import Pattern

SINGLE_PLACE: Final[int] = 1
ALIKE_PLACES: Final[int] = 2

Places = Annotated[int, Field(ge=SINGLE_PLACE)]
AlikePlaces = Annotated[int, Field(ge=ALIKE_PLACES)]


class Simple(Pattern, ABC):
    """A pattern that names a number of places and reads them itself.

    `places` is the whole of what one states, so `SameRank(places=3)` is three of a rank and `Run(places=5)`
    five in a row. Several decks in play let a rule reach further than one deck allows.
    """

    places: Places

    @property
    def size(self) -> int:
        return self.places
