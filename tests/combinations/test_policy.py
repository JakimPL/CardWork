from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.cards.cards import (
    ACE_OF_CLUBS,
    ACE_OF_SPADES,
    TWO_OF_CLUBS,
    TWO_OF_SPADES,
)
from cardwork.cards.orders import ACE_LOW_RANKS, RANK_SEQUENCE, SUIT_SEQUENCE
from cardwork.cards.rank import Rank, Ranks
from cardwork.cards.suit import Suit
from cardwork.combinations.policy import REGULAR_EVALUATION, Duplicates, Evaluation
from tests.cases import Case, descriptions

ACE_LOW_EVALUATION: Final[Evaluation] = Evaluation(
    ranks=ACE_LOW_RANKS,
    suits=SUIT_SEQUENCE,
    wheel=False,
    wild_jokers=True,
    duplicates=Duplicates.COUNT,
)
NO_WHEEL: Final[Evaluation] = Evaluation(
    ranks=RANK_SEQUENCE,
    suits=SUIT_SEQUENCE,
    wheel=False,
    wild_jokers=True,
    duplicates=Duplicates.COUNT,
)

SHORTEST_RUN: Final[int] = 2
POKER_HAND: Final[int] = 5
WHOLE_SEQUENCE: Final[int] = len(RANK_SEQUENCE)
PAST_THE_SEQUENCE: Final[int] = WHOLE_SEQUENCE + 1

ACE_HIGH_FIVE: Final[Ranks] = (Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE)
WHEEL_RANKS: Final[Ranks] = (Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE)
LOWEST_FIVE: Final[Ranks] = (Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX)


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
class StretchCase(Case):
    evaluation: Evaluation
    size: int
    stretched: int
    highest: Ranks
    lowest: Ranks
    low_ace: bool


STRETCHES: Final[tuple[StretchCase, ...]] = (
    StretchCase(
        description="five ranks stretch nine ways along the sequence and the wheel makes ten",
        evaluation=REGULAR_EVALUATION,
        size=POKER_HAND,
        stretched=WHOLE_SEQUENCE - POKER_HAND + SHORTEST_RUN,
        highest=ACE_HIGH_FIVE,
        lowest=WHEEL_RANKS,
        low_ace=True,
    ),
    StretchCase(
        description="a reading holding to its sequence stretches along it alone",
        evaluation=NO_WHEEL,
        size=POKER_HAND,
        stretched=WHOLE_SEQUENCE - POKER_HAND + 1,
        highest=ACE_HIGH_FIVE,
        lowest=LOWEST_FIVE,
        low_ace=False,
    ),
    StretchCase(
        description="two ranks stretch as far as the sequence reaches",
        evaluation=REGULAR_EVALUATION,
        size=SHORTEST_RUN,
        stretched=WHOLE_SEQUENCE,
        highest=(Rank.KING, Rank.ACE),
        lowest=(Rank.ACE, Rank.TWO),
        low_ace=True,
    ),
    StretchCase(
        description="the whole sequence stretches one way and the wheel turns it into another",
        evaluation=REGULAR_EVALUATION,
        size=WHOLE_SEQUENCE,
        stretched=SHORTEST_RUN,
        highest=RANK_SEQUENCE,
        lowest=(Rank.ACE, *RANK_SEQUENCE[:-1]),
        low_ace=True,
    ),
)


@pytest.mark.parametrize("case", STRETCHES, ids=descriptions(STRETCHES))
def test_a_reading_states_the_stretches_a_run_of_that_many_ranks_follows(case: StretchCase) -> None:
    stretched = case.evaluation.stretches(case.size)

    assert len(stretched) == case.stretched
    assert stretched[0].ranks == case.highest
    assert stretched[0].low_ace is False
    assert stretched[-1].ranks == case.lowest
    assert stretched[-1].low_ace is case.low_ace


def test_a_run_reaches_as_far_as_the_ranks_a_reading_places() -> None:
    assert REGULAR_EVALUATION.stretches(PAST_THE_SEQUENCE) == ()


def test_a_stretch_follows_two_ranks_at_the_least() -> None:
    with pytest.raises(ValueError, match="A run stretches over 2 ranks at the least, and 1 was asked for"):
        REGULAR_EVALUATION.stretches(1)


def test_the_wheel_stands_alone_among_the_stretches_that_read_an_ace_low() -> None:
    stretched = REGULAR_EVALUATION.stretches(POKER_HAND)

    assert [stretch.low_ace for stretch in stretched].count(True) == 1
    assert stretched[-1].ranks == WHEEL_RANKS


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
