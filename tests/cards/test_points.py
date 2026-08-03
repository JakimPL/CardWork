from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.cards.cards import (
    ACE_OF_HEARTS,
    BLACK_JOKER,
    JACK_OF_SPADES,
    KING_OF_DIAMONDS,
    NINE_OF_HEARTS,
    QUEEN_OF_CLUBS,
    RED_JOKER,
    TEN_OF_CLUBS,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardOrJoker
from cardwork.cards.points import ACE_LOW_POINTS, REGULAR_POINTS, PointTable
from cardwork.cards.rank import Rank

from ..cases import Case, descriptions


@dataclass(frozen=True)
class WorthCase(Case):
    card: CardOrJoker
    regular: int
    ace_low: int


WORTHS: Final[tuple[WorthCase, ...]] = (
    WorthCase(description="a pip card is worth its face", card=TWO_OF_SPADES, regular=2, ace_low=2),
    WorthCase(description="the nine is worth nine", card=NINE_OF_HEARTS, regular=9, ace_low=9),
    WorthCase(description="the ten is worth ten", card=TEN_OF_CLUBS, regular=10, ace_low=10),
    WorthCase(description="the jack is worth ten", card=JACK_OF_SPADES, regular=10, ace_low=10),
    WorthCase(description="the queen is worth ten", card=QUEEN_OF_CLUBS, regular=10, ace_low=10),
    WorthCase(description="the king is worth ten", card=KING_OF_DIAMONDS, regular=10, ace_low=10),
    WorthCase(description="the ace is worth ten, and one where it runs low", card=ACE_OF_HEARTS, regular=10, ace_low=1),
    WorthCase(description="a joker is worth nothing", card=RED_JOKER, regular=0, ace_low=0),
)


@pytest.mark.parametrize("case", WORTHS, ids=descriptions(WORTHS))
def test_both_tables_state_what_a_card_is_worth(case: WorthCase) -> None:
    assert REGULAR_POINTS.of(case.card) == case.regular
    assert ACE_LOW_POINTS.of(case.card) == case.ace_low


def test_a_total_counts_every_card_it_is_given() -> None:
    assert REGULAR_POINTS.total((TWO_OF_SPADES, TWO_OF_SPADES, ACE_OF_HEARTS)) == 14


def test_a_total_of_no_cards_is_nothing() -> None:
    assert REGULAR_POINTS.total(()) == 0


def test_a_total_counts_jokers_at_their_own_worth() -> None:
    jokers_only = PointTable(values=dict(REGULAR_POINTS.values), joker=5)

    assert jokers_only.total((BLACK_JOKER, RED_JOKER, TWO_OF_SPADES)) == 12


def test_a_table_scores_every_rank_of_the_deck() -> None:
    with pytest.raises(ValidationError, match="left out"):
        PointTable(values={Rank.TWO: 2}, joker=0)
