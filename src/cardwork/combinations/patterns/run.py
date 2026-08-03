from collections.abc import Iterator
from typing import Annotated, Final

from pydantic import Field

from cardwork.cards.rank import Rank, Ranks
from cardwork.combinations.demand import Demand
from cardwork.combinations.pattern import Reading
from cardwork.combinations.patterns.simple import ALIKE_PLACES, Simple
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.ordering.preorder import Key

LONGEST_RUN: Final[int] = len(Rank)
TOP_PLACE: Final[int] = -1

RunPlaces = Annotated[int, Field(ge=ALIKE_PLACES, le=LONGEST_RUN)]


class Run(Simple):
    """Places consecutive ranks fill, each of them asking for a rank of its own.

    An instance is settled by the card that tops it. The stretches follow the sequence the reading states, the
    highest-topped first, and where that reading admits the wheel one more stretch follows them: the highest
    rank beside the lowest ranks, which is A 2 3 4 5 over the regular sequence and is topped by its five. A run
    reaches as far as the ranks stretch, which is thirteen places over a standard deck.
    """

    places: RunPlaces

    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        for stretch, low_ace in self._stretches(evaluation):
            yield Shape(
                demands=tuple(Demand.of_rank(rank) for rank in stretch),
                low_ace=low_ace,
            )

    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        return (evaluation.rank_places()[reading[TOP_PLACE].rank],)

    def __str__(self) -> str:
        return f"a run of {self.places}"

    def _stretches(self, evaluation: Evaluation) -> Iterator[tuple[Ranks, bool]]:
        """Every stretch of that many consecutive ranks, the highest-topped first and each running upwards.

        Each stretch says whether it reads the highest rank as its lowest, which is what the wheel does.
        """
        ranks = evaluation.ranks
        for top in reversed(range(self.places - 1, len(ranks))):
            yield ranks[top + 1 - self.places : top + 1], False

        if evaluation.wheel:
            yield (ranks[TOP_PLACE], *ranks[: self.places - 1]), True
