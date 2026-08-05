from abc import ABC
from collections.abc import Iterator, Sequence
from itertools import product
from typing import Annotated, Final

from pydantic import Field

from cardwork.combinations.pattern import AnyPattern, Pattern
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape

PARTS: Final[int] = 2

Parts = Annotated[tuple[AnyPattern, ...], Field(min_length=PARTS)]


class Compound(Pattern, ABC):
    """A pattern made of others, which it names in the order they settle its strength.

    Two ways of making one stand below: `Together` reads one set of places by every part at once, and `Beside`
    gives each part places of its own. Either way an instance is settled by its parts in the order they are
    named, so the first part leads and the next breaks its ties.
    """

    parts: Parts

    def _listings(
        self,
        evaluation: Evaluation,
    ) -> tuple[tuple[Shape, ...], ...]:
        """The readings each part admits, each kept in the order that part gives them."""
        return tuple(tuple(part.shapes(evaluation)) for part in self.parts)

    @staticmethod
    def _choices(
        listings: Sequence[Sequence[Shape]],
    ) -> Iterator[tuple[int, ...]]:
        """Every way of taking one reading from each part, the strongest readings of the first part leading."""
        return product(*(range(len(listed)) for listed in listings))

    @staticmethod
    def _taken(
        listings: Sequence[Sequence[Shape]],
        chosen: Sequence[int],
    ) -> tuple[Shape, ...]:
        """The readings this choice names, one per part."""
        return tuple(
            listed[place]
            for listed, place in zip(
                listings,
                chosen,
                strict=True,
            )
        )
