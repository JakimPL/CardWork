from typing import Final

import pytest

from cardwork.cards.rank import Rank

PIPS: Final[frozenset[Rank]] = frozenset(
    {Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX, Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN}
)


@pytest.mark.parametrize("rank", tuple(Rank), ids=[rank.value for rank in Rank])
def test_a_rank_carries_a_numeric_face_from_the_two_up_to_the_ten(rank: Rank) -> None:
    assert rank.pip is (rank in PIPS)
