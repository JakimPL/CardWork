from collections.abc import Iterator
from typing import Literal

from cardwork.combinations.demand import ANY_CARD
from cardwork.combinations.pattern import Reading
from cardwork.combinations.patterns.simple import SINGLE_PLACE, Simple
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.ordering.preorder import Key


class AnyCards(Simple):
    """Places any card fills, which reads as a high card at one of them and as kickers beside a pair.

    An instance is settled by its ranks from the highest down, so that a hand keeping an ace stands above one
    keeping a king.
    """

    kind: Literal["any_cards"] = "any_cards"

    @property
    def alike(self) -> bool:
        return True

    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        yield Shape(demands=(ANY_CARD,) * self.places, low_ace=False)

    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        return self._descending_ranks(reading, evaluation)

    def __str__(self) -> str:
        return "any card" if self.places == SINGLE_PLACE else f"any {self.places} cards"
