from collections.abc import Iterator
from typing import Literal

from cardwork.combinations.demand import Demand
from cardwork.combinations.pattern import Reading
from cardwork.combinations.patterns.simple import AlikePlaces, Simple
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.ordering.preorder import Key


class SameSuit(Simple):
    """Places one suit fills, which reads as three of a suit at three of them and a flush at five.

    An instance is settled by the high cards it shows, read from the highest down, so a flush topped by an
    ace stands above one topped by a king and a tie on the ace is settled by the card below it.
    """

    kind: Literal["same_suit"] = "same_suit"
    places: AlikePlaces

    @property
    def alike(self) -> bool:
        return True

    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        for suit in reversed(evaluation.suits):
            yield Shape(
                demands=(Demand.of_suit(suit),) * self.places,
                low_ace=False,
            )

    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        return self._descending_ranks(reading, evaluation)

    def __str__(self) -> str:
        return f"{self.places} of a suit"
