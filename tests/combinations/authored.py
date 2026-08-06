from collections.abc import Iterator
from typing import Literal

from cardwork.cards.suit import Suit
from cardwork.combinations.demand import Demand
from cardwork.combinations.pattern import Pattern, Reading
from cardwork.combinations.patterns.simple import Places
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.ordering.preorder import Key


class OneSuit(Pattern):
    """Places one named suit fills, which stands here for the rule a game writes of its own.

    `cardwork` states its suited patterns over whichever suit a hand holds, so a rule naming the suit itself
    belongs to the game that wants it. This one carries a field of its own beside the places it takes, which is
    what makes it the test of a game-authored pattern travelling: the word, the class it reads back to and the
    game's own field all come back as they went out.
    """

    kind: Literal["one_suit"] = "one_suit"
    suit: Suit
    places: Places

    @property
    def size(self) -> int:
        return self.places

    @property
    def alike(self) -> bool:
        return True

    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        yield Shape(demands=(Demand.of_suit(self.suit),) * self.places, low_ace=False)

    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        return self._descending_ranks(reading, evaluation)

    def __str__(self) -> str:
        return f"{self.places} of {self.suit}"
