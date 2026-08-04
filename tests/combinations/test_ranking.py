from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.cards.card import Card
from cardwork.cards.cards import (
    ACE_OF_CLUBS,
    ACE_OF_SPADES,
    FIVE_OF_DIAMONDS,
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    FOUR_OF_CLUBS,
    JACK_OF_SPADES,
    KING_OF_CLUBS,
    KING_OF_DIAMONDS,
    KING_OF_HEARTS,
    KING_OF_SPADES,
    NINE_OF_SPADES,
    QUEEN_OF_SPADES,
    SEVEN_OF_DIAMONDS,
    SEVEN_OF_HEARTS,
    SEVEN_OF_SPADES,
    SIX_OF_SPADES,
    TEN_OF_SPADES,
    THREE_OF_CLUBS,
    THREE_OF_HEARTS,
    THREE_OF_SPADES,
    TWO_OF_CLUBS,
    TWO_OF_HEARTS,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardOrJoker
from cardwork.combinations.detect import find
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.patterns.same_suit import SameSuit
from cardwork.combinations.poker import (
    FLUSH,
    FULL_HOUSE,
    HIGH_CARD,
    PAIR,
    POKER,
    QUADRUPLET,
    STRAIGHT,
    STRAIGHT_FLUSH,
    TRIPLET,
    TWO_PAIR,
)
from cardwork.combinations.policy import REGULAR_EVALUATION
from cardwork.combinations.ranking import Ranking

THREE_OF_A_SUIT: Final[Pattern] = SameSuit(places=3)

from tests.cases import Case, descriptions

ROYAL_FLUSH: Final[tuple[CardOrJoker, ...]] = (
    TEN_OF_SPADES,
    JACK_OF_SPADES,
    QUEEN_OF_SPADES,
    KING_OF_SPADES,
    ACE_OF_SPADES,
)
FOUR_KINGS: Final[tuple[CardOrJoker, ...]] = (
    KING_OF_SPADES,
    KING_OF_HEARTS,
    KING_OF_CLUBS,
    KING_OF_DIAMONDS,
    TWO_OF_SPADES,
)
KINGS_OVER_FIVES: Final[tuple[CardOrJoker, ...]] = (
    KING_OF_SPADES,
    KING_OF_HEARTS,
    KING_OF_CLUBS,
    FIVE_OF_SPADES,
    FIVE_OF_HEARTS,
)
SPADE_FLUSH: Final[tuple[CardOrJoker, ...]] = (
    ACE_OF_SPADES,
    NINE_OF_SPADES,
    FIVE_OF_SPADES,
    THREE_OF_SPADES,
    TWO_OF_SPADES,
)
SIX_HIGH_STRAIGHT: Final[tuple[CardOrJoker, ...]] = (
    TWO_OF_SPADES,
    THREE_OF_HEARTS,
    FOUR_OF_CLUBS,
    FIVE_OF_DIAMONDS,
    SIX_OF_SPADES,
)
WHEEL: Final[tuple[CardOrJoker, ...]] = (
    ACE_OF_SPADES,
    TWO_OF_HEARTS,
    THREE_OF_CLUBS,
    FOUR_OF_CLUBS,
    FIVE_OF_SPADES,
)
KINGS: Final[tuple[CardOrJoker, ...]] = (KING_OF_SPADES, KING_OF_HEARTS, TWO_OF_CLUBS)
OTHER_KINGS: Final[tuple[CardOrJoker, ...]] = (KING_OF_DIAMONDS, KING_OF_CLUBS, THREE_OF_CLUBS)
FIVES: Final[tuple[CardOrJoker, ...]] = (FIVE_OF_SPADES, FIVE_OF_HEARTS, TWO_OF_CLUBS)


@dataclass(frozen=True)
class StrongestCase(Case):
    cards: tuple[CardOrJoker, ...]
    pattern: Pattern | None
    reading: tuple[Card, ...] | None


STRONGEST: Final[tuple[StrongestCase, ...]] = (
    StrongestCase(
        description="five spades in a row are a straight flush",
        cards=ROYAL_FLUSH,
        pattern=STRAIGHT_FLUSH,
        reading=(TEN_OF_SPADES, JACK_OF_SPADES, QUEEN_OF_SPADES, KING_OF_SPADES, ACE_OF_SPADES),
    ),
    StrongestCase(
        description="four kings are a quadruplet",
        cards=FOUR_KINGS,
        pattern=QUADRUPLET,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_DIAMONDS, KING_OF_CLUBS),
    ),
    StrongestCase(
        description="three kings and two fives are a full house",
        cards=KINGS_OVER_FIVES,
        pattern=FULL_HOUSE,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS, FIVE_OF_SPADES, FIVE_OF_HEARTS),
    ),
    StrongestCase(
        description="five spades out of order are a flush",
        cards=SPADE_FLUSH,
        pattern=FLUSH,
        reading=(ACE_OF_SPADES, NINE_OF_SPADES, FIVE_OF_SPADES, THREE_OF_SPADES, TWO_OF_SPADES),
    ),
    StrongestCase(
        description="a run in mixed suits is a straight",
        cards=SIX_HIGH_STRAIGHT,
        pattern=STRAIGHT,
        reading=(TWO_OF_SPADES, THREE_OF_HEARTS, FOUR_OF_CLUBS, FIVE_OF_DIAMONDS, SIX_OF_SPADES),
    ),
    StrongestCase(
        description="three sevens beside two odd cards are a triplet",
        cards=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS, TWO_OF_CLUBS, THREE_OF_HEARTS),
        pattern=TRIPLET,
        reading=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS),
    ),
    StrongestCase(
        description="two kings and two fives are two pair",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, FIVE_OF_SPADES, FIVE_OF_HEARTS, TWO_OF_CLUBS),
        pattern=TWO_PAIR,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, FIVE_OF_SPADES, FIVE_OF_HEARTS),
    ),
    StrongestCase(
        description="two kings alone are a pair",
        cards=KINGS,
        pattern=PAIR,
        reading=(KING_OF_SPADES, KING_OF_HEARTS),
    ),
    StrongestCase(
        description="unrelated cards are the highest of them",
        cards=(KING_OF_SPADES, FIVE_OF_HEARTS, TWO_OF_CLUBS),
        pattern=HIGH_CARD,
        reading=(KING_OF_SPADES,),
    ),
    StrongestCase(description="no cards form nothing", cards=(), pattern=None, reading=None),
)


@pytest.mark.parametrize("case", STRONGEST, ids=descriptions(STRONGEST))
def test_a_ranking_reads_the_best_combination_a_hand_forms(case: StrongestCase) -> None:
    found = POKER.strongest(case.cards)

    assert (found.pattern if found is not None else None) == case.pattern
    assert (found.reading if found is not None else None) == case.reading


@dataclass(frozen=True)
class ContestCase(Case):
    left: tuple[CardOrJoker, ...]
    right: tuple[CardOrJoker, ...]
    comparison: int
    equivalent: bool


CONTESTS: Final[tuple[ContestCase, ...]] = (
    ContestCase(
        description="a straight flush beats a quadruplet",
        left=ROYAL_FLUSH,
        right=FOUR_KINGS,
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="a quadruplet beats a full house",
        left=FOUR_KINGS,
        right=KINGS_OVER_FIVES,
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="a full house beats a flush",
        left=KINGS_OVER_FIVES,
        right=SPADE_FLUSH,
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="a flush beats a straight",
        left=SPADE_FLUSH,
        right=SIX_HIGH_STRAIGHT,
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="a straight beats two pair",
        left=SIX_HIGH_STRAIGHT,
        right=(KING_OF_SPADES, KING_OF_HEARTS, FIVE_OF_SPADES, FIVE_OF_HEARTS, TWO_OF_CLUBS),
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="the higher pair takes the contest",
        left=KINGS,
        right=FIVES,
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="two pairs of kings stand alongside each other",
        left=KINGS,
        right=OTHER_KINGS,
        comparison=0,
        equivalent=True,
    ),
    ContestCase(
        description="the wheel stands below a six-high straight",
        left=WHEEL,
        right=SIX_HIGH_STRAIGHT,
        comparison=-1,
        equivalent=False,
    ),
)


@pytest.mark.parametrize("case", CONTESTS, ids=descriptions(CONTESTS))
def test_a_ranking_settles_one_hand_against_another(case: ContestCase) -> None:
    order = POKER.order
    left = POKER.strongest(case.left)
    right = POKER.strongest(case.right)

    assert left is not None
    assert right is not None
    assert order.compare(left, right) == case.comparison
    assert order.equivalent(left, right) is case.equivalent


def test_a_ranking_picks_the_winners_out_of_a_table() -> None:
    order = POKER.order
    hands = tuple(POKER.strongest(cards) for cards in (FIVES, ROYAL_FLUSH, KINGS))

    assert order.argmaxima(hands) == (1,)
    assert order.argminima(hands) == (0,)


def test_a_ranking_names_every_seat_that_shares_the_top() -> None:
    order = POKER.order
    hands = tuple(POKER.strongest(cards) for cards in (KINGS, FIVES, OTHER_KINGS))

    assert order.argmaxima(hands) == (0, 2)


def test_a_ranking_answers_for_the_patterns_it_lists() -> None:
    three_of_a_suit = find((KING_OF_SPADES, NINE_OF_SPADES, TWO_OF_SPADES), THREE_OF_A_SUIT, REGULAR_EVALUATION)

    assert three_of_a_suit is not None
    with pytest.raises(KeyError, match="takes no place"):
        POKER.order.key(three_of_a_suit)


def test_a_ranking_gives_every_pattern_one_place() -> None:
    with pytest.raises(ValidationError, match="Every pattern takes one place"):
        Ranking(patterns=(PAIR, TRIPLET, PAIR), evaluation=REGULAR_EVALUATION)


def test_a_ranking_recognises_a_combination_at_the_least() -> None:
    with pytest.raises(ValidationError, match="at least 1 item"):
        Ranking(patterns=(), evaluation=REGULAR_EVALUATION)


def test_a_ranking_of_its_own_answers_only_the_combinations_it_names() -> None:
    suits_alone = Ranking(patterns=(THREE_OF_A_SUIT,), evaluation=REGULAR_EVALUATION)

    found = suits_alone.strongest((KING_OF_SPADES, NINE_OF_SPADES, TWO_OF_SPADES, ACE_OF_CLUBS))

    assert found is not None
    assert found.pattern == THREE_OF_A_SUIT
    assert suits_alone.strongest((KING_OF_SPADES, NINE_OF_SPADES, ACE_OF_CLUBS)) is None
