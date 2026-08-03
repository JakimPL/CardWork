from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.cards.card import Card
from cardwork.cards.cards import (
    ACE_OF_CLUBS,
    ACE_OF_SPADES,
    FOUR_OF_CLUBS,
    FOUR_OF_SPADES,
    KING_OF_SPADES,
    NINE_OF_CLUBS,
    QUEEN_OF_HEARTS,
    QUEEN_OF_SPADES,
    SEVEN_OF_HEARTS,
    SEVEN_OF_SPADES,
    THREE_OF_CLUBS,
    TWO_OF_CLUBS,
    TWO_OF_SPADES,
)
from cardwork.cards.order import ACE_LOW_RANKS, BY_RANK, BY_RANK_ACE_LOW, BY_SUIT, RANK_SEQUENCE, REGULAR_ORDER
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.decks.standard import STANDARD_DECK

from ..cases import Case, descriptions


@dataclass(frozen=True)
class CardOrderCase(Case):
    left: Card
    right: Card
    by_rank: int
    regular: int


CARD_ORDERS: Final[tuple[CardOrderCase, ...]] = (
    CardOrderCase(
        description="a higher rank outranks a lower one whatever the suits",
        left=NINE_OF_CLUBS,
        right=FOUR_OF_SPADES,
        by_rank=1,
        regular=1,
    ),
    CardOrderCase(
        description="the two stands at the foot of both orders",
        left=TWO_OF_SPADES,
        right=THREE_OF_CLUBS,
        by_rank=-1,
        regular=-1,
    ),
    CardOrderCase(
        description="the ace stands at the top of both orders",
        left=ACE_OF_CLUBS,
        right=KING_OF_SPADES,
        by_rank=1,
        regular=1,
    ),
    CardOrderCase(
        description="one rank in two suits ties by rank and parts by suit",
        left=SEVEN_OF_HEARTS,
        right=SEVEN_OF_SPADES,
        by_rank=0,
        regular=-1,
    ),
    CardOrderCase(
        description="a card sits alongside itself in both orders",
        left=FOUR_OF_CLUBS,
        right=FOUR_OF_CLUBS,
        by_rank=0,
        regular=0,
    ),
)


@pytest.mark.parametrize("case", CARD_ORDERS, ids=descriptions(CARD_ORDERS))
def test_the_rank_order_and_the_regular_order_place_a_pair_of_cards(case: CardOrderCase) -> None:
    assert BY_RANK.compare(case.left, case.right) == case.by_rank
    assert REGULAR_ORDER.compare(case.left, case.right) == case.regular


def test_the_rank_sequence_runs_from_the_two_up_to_the_ace() -> None:
    assert RANK_SEQUENCE[0] is Rank.TWO
    assert RANK_SEQUENCE[-1] is Rank.ACE
    assert len(RANK_SEQUENCE) == len(Rank)


def test_the_ace_low_sequence_opens_with_the_ace_and_closes_with_the_king() -> None:
    assert ACE_LOW_RANKS[0] is Rank.ACE
    assert ACE_LOW_RANKS[1] is Rank.TWO
    assert ACE_LOW_RANKS[-1] is Rank.KING


def test_the_ace_low_order_puts_the_ace_below_the_two() -> None:
    assert BY_RANK_ACE_LOW.compare(ACE_OF_SPADES, TWO_OF_CLUBS) == -1


def test_the_suit_order_raises_the_spade_above_every_other_suit() -> None:
    highest = BY_SUIT.maxima(tuple(Card(rank=Rank.TWO, suit=suit) for suit in Suit))

    assert highest == (Card(rank=Rank.TWO, suit=Suit.SPADE),)


def test_the_regular_order_places_every_card_of_a_standard_deck_apart() -> None:
    places = {REGULAR_ORDER.key(card) for card in STANDARD_DECK if isinstance(card, Card)}

    assert len(places) == len(STANDARD_DECK)


def test_the_regular_order_settles_a_tie_of_rank_by_the_suit() -> None:
    revealed = (QUEEN_OF_HEARTS, QUEEN_OF_SPADES, FOUR_OF_CLUBS)

    assert REGULAR_ORDER.maxima(revealed) == (QUEEN_OF_SPADES,)
    assert REGULAR_ORDER.argmaxima(revealed) == (1,)


def test_the_rank_order_holds_every_card_of_one_rank_at_the_top_together() -> None:
    revealed = (QUEEN_OF_HEARTS, QUEEN_OF_SPADES, FOUR_OF_CLUBS)

    assert BY_RANK.maxima(revealed) == (QUEEN_OF_HEARTS, QUEEN_OF_SPADES)
    assert BY_RANK.argmaxima(revealed) == (0, 1)
