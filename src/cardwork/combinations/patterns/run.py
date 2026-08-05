from collections.abc import Iterator
from typing import Annotated, Final, Literal

from pydantic import Field

from cardwork.cards.rank import Rank
from cardwork.combinations.demand import Demand
from cardwork.combinations.pattern import Reading
from cardwork.combinations.patterns.simple import Simple
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.combinations.stretch import SHORTEST_STRETCH
from cardwork.ordering.preorder import Key

LONGEST_RUN: Final[int] = len(Rank)
TOP_PLACE: Final[int] = -1

RunPlaces = Annotated[int, Field(ge=SHORTEST_STRETCH, le=LONGEST_RUN)]


class Run(Simple):
    """Places consecutive ranks fill, each of them asking for a rank of its own.

    An instance is settled by the card that tops it. The rule is read over the stretches the reading admits,
    which `Evaluation.stretches` states, so a run reaches as far as those ranks stretch and takes thirteen
    places over a standard deck.
    """

    kind: Literal["run"] = "run"
    places: RunPlaces

    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        for stretch in evaluation.stretches(self.places):
            yield Shape(
                demands=tuple(Demand.of_rank(rank) for rank in stretch.ranks),
                low_ace=stretch.low_ace,
            )

    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        return (evaluation.rank_places()[reading[TOP_PLACE].rank],)

    def __str__(self) -> str:
        return f"a run of {self.places}"
