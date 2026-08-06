from collections.abc import Iterator
from typing import Final, Literal

from cardwork.combinations.demand import Demand
from cardwork.combinations.pattern import Reading
from cardwork.combinations.patterns.simple import AlikePlaces, Simple
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.ordering.preorder import Key

FIRST_PLACE: Final[int] = 0


class SameRank(Simple):
    """Places one rank fills, which reads as a pair at two of them and a triplet at three.

    An instance is settled by the rank it holds, so a pair of kings stands above a pair of queens. Several
    decks in play let the rule reach further, so five of a rank stands where two decks are dealt.
    """

    kind: Literal["same_rank"] = "same_rank"
    places: AlikePlaces

    @property
    def alike(self) -> bool:
        return True

    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        for rank in reversed(evaluation.ranks):
            yield Shape(
                demands=(Demand.of_rank(rank),) * self.places,
                low_ace=False,
            )

    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        return (evaluation.rank_places()[reading[FIRST_PLACE].rank],)

    def __str__(self) -> str:
        return f"{self.places} of a rank"
