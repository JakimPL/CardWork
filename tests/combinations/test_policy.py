from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.cards.cards import ACE_OF_CLUBS, ACE_OF_SPADES, TWO_OF_CLUBS, TWO_OF_SPADES
from cardwork.cards.order import ACE_LOW_RANKS, RANK_SEQUENCE, SUIT_SEQUENCE
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.combinations.policy import REGULAR_EVALUATION, Duplicates, Evaluation

from ..cases import Case, descriptions

ACE_LOW_EVALUATION: Final[Evaluation] = Evaluation(
    ranks=ACE_LOW_RANKS,
    suits=SUIT_SEQUENCE,
    wheel=False,
    wild_jokers=True,
    duplicates=Duplicates.COUNT,
)


def test_the_regular_reading_runs_from_the_two_up_to_the_ace() -> None:
    places = REGULAR_EVALUATION.rank_places()

    assert places[Rank.TWO] == 0
    assert places[Rank.ACE] == len(RANK_SEQUENCE) - 1


def test_a_reading_places_the_ace_where_it_lists_it() -> None:
    assert ACE_LOW_EVALUATION.rank_places()[Rank.ACE] == 0


def test_a_reading_gives_a_single_card_its_rank_and_then_its_suit() -> None:
    order = REGULAR_EVALUATION.card_order()

    assert order.compare(TWO_OF_SPADES, ACE_OF_CLUBS) == -1
    assert order.compare(ACE_OF_SPADES, ACE_OF_CLUBS) == 1
    assert order.maxima((TWO_OF_CLUBS, ACE_OF_SPADES, ACE_OF_CLUBS)) == (ACE_OF_SPADES,)


@dataclass(frozen=True)
class RefusedCase(Case):
    ranks: tuple[Rank, ...]
    suits: tuple[Suit, ...]
    complaint: str


REFUSED: Final[tuple[RefusedCase, ...]] = (
    RefusedCase(
        description="a rank of the deck left out",
        ranks=RANK_SEQUENCE[1:],
        suits=SUIT_SEQUENCE,
        complaint="every rank of the deck, and these are left out",
    ),
    RefusedCase(
        description="a suit of the deck left out",
        ranks=RANK_SEQUENCE,
        suits=SUIT_SEQUENCE[1:],
        complaint="every suit of the deck, and these are left out",
    ),
    RefusedCase(
        description="a rank listed twice",
        ranks=(*RANK_SEQUENCE, Rank.ACE),
        suits=SUIT_SEQUENCE,
        complaint="Every rank takes one place",
    ),
    RefusedCase(
        description="a suit listed twice",
        ranks=RANK_SEQUENCE,
        suits=(*SUIT_SEQUENCE, Suit.SPADE),
        complaint="Every suit takes one place",
    ),
)


@pytest.mark.parametrize("case", REFUSED, ids=descriptions(REFUSED))
def test_a_reading_gives_every_card_of_the_deck_one_place(case: RefusedCase) -> None:
    with pytest.raises(ValidationError, match=case.complaint):
        Evaluation(
            ranks=case.ranks,
            suits=case.suits,
            wheel=True,
            wild_jokers=True,
            duplicates=Duplicates.COUNT,
        )
