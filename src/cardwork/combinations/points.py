from typing import Final

from cardwork.cards.points import ACE_LOW_POINTS, REGULAR_POINTS, PointTable
from cardwork.combinations.combination import Combination
from cardwork.models.base import BaseFrozen


class Scoring(BaseFrozen):
    """What a combination is worth to a game that counts it.

    Two tables state it, because one rank changes worth with the company it keeps: a run that reads its
    highest rank as its lowest is counted by `low_ace_table`, which is where the ace of A 2 3 4 5 is worth
    one, and every other combination is counted by `table`.

    Counting reads what each card of the combination stands for, so a joker standing in for the four of hearts
    is worth four.
    """

    table: PointTable
    low_ace_table: PointTable

    def of(self, combination: Combination) -> int:
        """What the combination is worth here."""
        return self._table_for(combination).total(combination.reading)

    def _table_for(self, combination: Combination) -> PointTable:
        return self.low_ace_table if combination.low_ace else self.table


REGULAR_SCORING: Final[Scoring] = Scoring(
    table=REGULAR_POINTS,
    low_ace_table=ACE_LOW_POINTS,
)
