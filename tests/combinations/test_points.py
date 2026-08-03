from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.cards.cards import (
    ACE_OF_SPADES,
    FIVE_OF_DIAMONDS,
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    FOUR_OF_CLUBS,
    FOUR_OF_DIAMONDS,
    FOUR_OF_SPADES,
    JACK_OF_SPADES,
    KING_OF_CLUBS,
    KING_OF_HEARTS,
    KING_OF_SPADES,
    NINE_OF_SPADES,
    QUEEN_OF_SPADES,
    RED_JOKER,
    SEVEN_OF_HEARTS,
    SEVEN_OF_SPADES,
    SIX_OF_SPADES,
    TEN_OF_SPADES,
    THREE_OF_CLUBS,
    THREE_OF_HEARTS,
    THREE_OF_SPADES,
    TWO_OF_HEARTS,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardOrJoker
from cardwork.combinations.detect import find
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.patterns.same_suit import SameSuit
from cardwork.combinations.points import REGULAR_SCORING
from cardwork.combinations.poker import FULL_HOUSE, HIGH_CARD, STRAIGHT, STRAIGHT_FLUSH, TRIPLET
from cardwork.combinations.policy import REGULAR_EVALUATION

THREE_OF_A_SUIT: Final[Pattern] = SameSuit(places=3)

from ..cases import Case, descriptions


@dataclass(frozen=True)
class WorthCase(Case):
    cards: tuple[CardOrJoker, ...]
    pattern: Pattern
    points: int


WORTHS: Final[tuple[WorthCase, ...]] = (
    WorthCase(
        description="the ace of the wheel counts as one",
        cards=(ACE_OF_SPADES, TWO_OF_HEARTS, THREE_OF_CLUBS, FOUR_OF_DIAMONDS, FIVE_OF_SPADES),
        pattern=STRAIGHT,
        points=1 + 2 + 3 + 4 + 5,
    ),
    WorthCase(
        description="the ace of a wheel in one suit counts as one likewise",
        cards=(ACE_OF_SPADES, TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES),
        pattern=STRAIGHT_FLUSH,
        points=1 + 2 + 3 + 4 + 5,
    ),
    WorthCase(
        description="a run of pips counts each of its faces",
        cards=(TWO_OF_SPADES, THREE_OF_HEARTS, FOUR_OF_CLUBS, FIVE_OF_DIAMONDS, SIX_OF_SPADES),
        pattern=STRAIGHT,
        points=2 + 3 + 4 + 5 + 6,
    ),
    WorthCase(
        description="a run up to the ace counts every card at ten",
        cards=(TEN_OF_SPADES, JACK_OF_SPADES, QUEEN_OF_SPADES, KING_OF_SPADES, ACE_OF_SPADES),
        pattern=STRAIGHT,
        points=10 * 5,
    ),
    WorthCase(
        description="a triplet of sevens is worth three sevens",
        cards=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, THREE_OF_SPADES, RED_JOKER),
        pattern=TRIPLET,
        points=7 * 3,
    ),
    WorthCase(
        description="three kings over two fives count the figures at ten",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS, FIVE_OF_SPADES, FIVE_OF_HEARTS),
        pattern=FULL_HOUSE,
        points=10 * 3 + 5 * 2,
    ),
    WorthCase(
        description="three of a suit counts the three cards it names",
        cards=(KING_OF_SPADES, NINE_OF_SPADES, TWO_OF_SPADES, THREE_OF_HEARTS),
        pattern=THREE_OF_A_SUIT,
        points=10 + 9 + 2,
    ),
    WorthCase(
        description="a single counts the one card it names",
        cards=(ACE_OF_SPADES, FIVE_OF_HEARTS),
        pattern=HIGH_CARD,
        points=10,
    ),
)


@pytest.mark.parametrize("case", WORTHS, ids=descriptions(WORTHS))
def test_a_scoring_counts_the_cards_a_combination_reads_as(case: WorthCase) -> None:
    found = find(case.cards, case.pattern, REGULAR_EVALUATION)

    assert found is not None
    assert REGULAR_SCORING.of(found) == case.points
