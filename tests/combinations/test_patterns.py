from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.cards.cards import (
    ACE_OF_HEARTS,
    ACE_OF_SPADES,
    FIVE_OF_CLUBS,
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    FOUR_OF_CLUBS,
    FOUR_OF_SPADES,
    JACK_OF_SPADES,
    KING_OF_HEARTS,
    KING_OF_SPADES,
    NINE_OF_CLUBS,
    QUEEN_OF_SPADES,
    SEVEN_OF_HEARTS,
    TEN_OF_SPADES,
    THREE_OF_CLUBS,
    THREE_OF_SPADES,
    TWO_OF_DIAMONDS,
    TWO_OF_HEARTS,
    TWO_OF_SPADES,
)
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.combinations.demand import ANY_CARD, Demand
from cardwork.combinations.pattern import Pattern, Reading
from cardwork.combinations.patterns.any_cards import AnyCards
from cardwork.combinations.patterns.beside import Beside
from cardwork.combinations.patterns.run import Run
from cardwork.combinations.patterns.same_rank import SameRank
from cardwork.combinations.patterns.same_suit import SameSuit
from cardwork.combinations.patterns.together import Together
from cardwork.combinations.poker import (
    FLUSH,
    FULL_HOUSE,
    HIGH_CARD,
    PAIR,
    POKER_HAND,
    QUADRUPLET,
    STRAIGHT,
    STRAIGHT_FLUSH,
    TRIPLET,
    TWO_PAIR,
    WHEEL,
)
from cardwork.combinations.policy import REGULAR_EVALUATION, Duplicates, Evaluation
from cardwork.ordering.preorder import Key

from ..cases import Case, descriptions

PLACES: Final[Mapping[Rank, int]] = REGULAR_EVALUATION.rank_places()
SUITED_PLACES: Final[int] = 3
NO_WHEEL: Final[Evaluation] = Evaluation(
    ranks=REGULAR_EVALUATION.ranks,
    suits=REGULAR_EVALUATION.suits,
    wheel=False,
    wild_jokers=True,
    duplicates=Duplicates.COUNT,
)
RUN_TO_THE_ACE: Final[tuple[Rank, ...]] = (Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE)

THREE_OF_A_SUIT: Final[Pattern] = SameSuit(places=SUITED_PLACES)
FIVE_OF_A_RANK: Final[Pattern] = SameRank(places=5)
LONGEST_RUN: Final[Pattern] = Run(places=len(Rank))
ONE_PAIR: Final[Pattern] = Beside(parts=(PAIR, AnyCards(places=3)))
LOOSE_BESIDE_LOOSE: Final[Pattern] = Beside(parts=(AnyCards(places=2), AnyCards(places=2)))
SUITED_PAIR: Final[Pattern] = Together(parts=(PAIR, SameSuit(places=2)))


def _ranks(*ranks: Rank) -> tuple[Demand, ...]:
    return tuple(Demand.of_rank(rank) for rank in ranks)


def _suit(suit: Suit, places: int) -> tuple[Demand, ...]:
    return tuple(Demand.of_suit(suit) for _ in range(places))


def _cards(suit: Suit, *ranks: Rank) -> tuple[Demand, ...]:
    return tuple(Demand(rank=rank, suit=suit) for rank in ranks)


@dataclass(frozen=True)
class ShapesCase(Case):
    pattern: Pattern
    size: int
    shapes: int
    strongest: tuple[Demand, ...]


SHAPES: Final[tuple[ShapesCase, ...]] = (
    ShapesCase(
        description="a loose place reads one way, taking any card",
        pattern=HIGH_CARD,
        size=1,
        shapes=1,
        strongest=(ANY_CARD,),
    ),
    ShapesCase(
        description="a pair reads one way per rank",
        pattern=PAIR,
        size=2,
        shapes=len(Rank),
        strongest=_ranks(Rank.ACE, Rank.ACE),
    ),
    ShapesCase(
        description="a triplet reads one way per rank",
        pattern=TRIPLET,
        size=3,
        shapes=len(Rank),
        strongest=_ranks(Rank.ACE, Rank.ACE, Rank.ACE),
    ),
    ShapesCase(
        description="a quadruplet reads one way per rank",
        pattern=QUADRUPLET,
        size=4,
        shapes=len(Rank),
        strongest=_ranks(Rank.ACE, Rank.ACE, Rank.ACE, Rank.ACE),
    ),
    ShapesCase(
        description="five of a rank reads one way per rank, which two decks reach",
        pattern=FIVE_OF_A_RANK,
        size=5,
        shapes=len(Rank),
        strongest=_ranks(*(Rank.ACE,) * 5),
    ),
    ShapesCase(
        description="two pair read one way per pair of ranks, the higher named first",
        pattern=TWO_PAIR,
        size=4,
        shapes=len(Rank) * (len(Rank) - 1) // 2,
        strongest=_ranks(Rank.ACE, Rank.ACE, Rank.KING, Rank.KING),
    ),
    ShapesCase(
        description="a full house reads one way per ordered pair of ranks",
        pattern=FULL_HOUSE,
        size=5,
        shapes=len(Rank) * (len(Rank) - 1),
        strongest=_ranks(Rank.ACE, Rank.ACE, Rank.ACE, Rank.KING, Rank.KING),
    ),
    ShapesCase(
        description="a pair beside loose places reads one way per rank",
        pattern=ONE_PAIR,
        size=5,
        shapes=len(Rank),
        strongest=(*_ranks(Rank.ACE, Rank.ACE), *(ANY_CARD,) * 3),
    ),
    ShapesCase(
        description="loose places beside loose places read as one run of them",
        pattern=LOOSE_BESIDE_LOOSE,
        size=4,
        shapes=1,
        strongest=(ANY_CARD,) * 4,
    ),
    ShapesCase(
        description="a run of five reads one way per stretch, the wheel besides",
        pattern=STRAIGHT,
        size=POKER_HAND,
        shapes=len(Rank) - POKER_HAND + 2,
        strongest=_ranks(*RUN_TO_THE_ACE),
    ),
    ShapesCase(
        description="a run of thirteen reads the whole sequence, and the wheel turns it once",
        pattern=LONGEST_RUN,
        size=len(Rank),
        shapes=2,
        strongest=_ranks(*REGULAR_EVALUATION.ranks),
    ),
    ShapesCase(
        description="a flush reads one way per suit",
        pattern=THREE_OF_A_SUIT,
        size=SUITED_PLACES,
        shapes=len(Suit),
        strongest=_suit(Suit.SPADE, SUITED_PLACES),
    ),
    ShapesCase(
        description="a suited run reads one way per stretch and suit",
        pattern=STRAIGHT_FLUSH,
        size=POKER_HAND,
        shapes=(len(Rank) - POKER_HAND + 2) * len(Suit),
        strongest=_cards(Suit.SPADE, *RUN_TO_THE_ACE),
    ),
    ShapesCase(
        description="a suited pair reads one way per rank and suit",
        pattern=SUITED_PAIR,
        size=2,
        shapes=len(Rank) * len(Suit),
        strongest=_cards(Suit.SPADE, Rank.ACE, Rank.ACE),
    ),
)


@pytest.mark.parametrize("case", SHAPES, ids=descriptions(SHAPES))
def test_a_pattern_states_the_readings_it_admits(case: ShapesCase) -> None:
    admitted = tuple(case.pattern.shapes(REGULAR_EVALUATION))

    assert case.pattern.size == case.size
    assert len(admitted) == case.shapes
    assert admitted[0].demands == case.strongest
    assert all(shape.size == case.size for shape in admitted)


@dataclass(frozen=True)
class StrengthCase(Case):
    pattern: Pattern
    reading: Reading
    key: Key


STRENGTHS: Final[tuple[StrengthCase, ...]] = (
    StrengthCase(
        description="a pair reads the rank it holds",
        pattern=PAIR,
        reading=(KING_OF_SPADES, KING_OF_HEARTS),
        key=(PLACES[Rank.KING],),
    ),
    StrengthCase(
        description="a flush reads its high cards from the top down",
        pattern=THREE_OF_A_SUIT,
        reading=(ACE_OF_SPADES, TWO_OF_SPADES, THREE_OF_SPADES),
        key=(PLACES[Rank.ACE], PLACES[Rank.THREE], PLACES[Rank.TWO]),
    ),
    StrengthCase(
        description="a run reads the card that tops it",
        pattern=STRAIGHT,
        reading=(TEN_OF_SPADES, JACK_OF_SPADES, QUEEN_OF_SPADES, KING_OF_HEARTS, ACE_OF_SPADES),
        key=(PLACES[Rank.ACE],),
    ),
    StrengthCase(
        description="the wheel is topped by its five",
        pattern=STRAIGHT,
        reading=(ACE_OF_SPADES, TWO_OF_HEARTS, THREE_OF_CLUBS, FOUR_OF_CLUBS, FIVE_OF_SPADES),
        key=(PLACES[Rank.FIVE],),
    ),
    StrengthCase(
        description="a full house leads with the rank of its triplet",
        pattern=FULL_HOUSE,
        reading=(TWO_OF_SPADES, TWO_OF_HEARTS, TWO_OF_DIAMONDS, ACE_OF_SPADES, ACE_OF_HEARTS),
        key=(PLACES[Rank.TWO], PLACES[Rank.ACE]),
    ),
    StrengthCase(
        description="two pair read the higher pair and then the lower",
        pattern=TWO_PAIR,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, TWO_OF_SPADES, TWO_OF_HEARTS),
        key=(PLACES[Rank.KING], PLACES[Rank.TWO]),
    ),
    StrengthCase(
        description="a pair beside loose places is settled by the pair and then by the cards around it",
        pattern=ONE_PAIR,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, NINE_OF_CLUBS, SEVEN_OF_HEARTS, TWO_OF_DIAMONDS),
        key=(PLACES[Rank.KING], PLACES[Rank.NINE], PLACES[Rank.SEVEN], PLACES[Rank.TWO]),
    ),
    StrengthCase(
        description="a suited run reads the run first and the suited cards after it",
        pattern=STRAIGHT_FLUSH,
        reading=(ACE_OF_SPADES, TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES),
        key=(
            PLACES[Rank.FIVE],
            PLACES[Rank.ACE],
            PLACES[Rank.FIVE],
            PLACES[Rank.FOUR],
            PLACES[Rank.THREE],
            PLACES[Rank.TWO],
        ),
    ),
    StrengthCase(
        description="a loose place reads the card standing on it",
        pattern=HIGH_CARD,
        reading=(ACE_OF_SPADES,),
        key=(PLACES[Rank.ACE],),
    ),
)


@pytest.mark.parametrize("case", STRENGTHS, ids=descriptions(STRENGTHS))
def test_a_pattern_states_where_a_reading_of_it_stands(case: StrengthCase) -> None:
    assert case.pattern.strength(case.reading, REGULAR_EVALUATION) == case.key


@dataclass(frozen=True)
class WordsCase(Case):
    pattern: Pattern
    words: str


WORDS: Final[tuple[WordsCase, ...]] = (
    WordsCase(description="a loose place", pattern=HIGH_CARD, words="any card"),
    WordsCase(description="several loose places", pattern=AnyCards(places=3), words="any 3 cards"),
    WordsCase(description="a pair", pattern=PAIR, words="2 of a rank"),
    WordsCase(description="a flush", pattern=FLUSH, words="5 of a suit"),
    WordsCase(description="a run", pattern=STRAIGHT, words="a run of 5"),
    WordsCase(description="two pair", pattern=TWO_PAIR, words="2 of a rank beside 2 of a rank"),
    WordsCase(description="a full house", pattern=FULL_HOUSE, words="3 of a rank beside 2 of a rank"),
    WordsCase(
        description="a pair with kickers",
        pattern=ONE_PAIR,
        words="2 of a rank beside any 3 cards",
    ),
    WordsCase(
        description="a straight flush",
        pattern=STRAIGHT_FLUSH,
        words="a run of 5 together with 5 of a suit",
    ),
)


@pytest.mark.parametrize("case", WORDS, ids=descriptions(WORDS))
def test_a_pattern_states_itself_in_words(case: WordsCase) -> None:
    assert str(case.pattern) == case.words
    assert repr(case.pattern) == case.words


@dataclass(frozen=True)
class RefusedPlacesCase(Case):
    pattern: type[SameRank] | type[SameSuit] | type[Run] | type[AnyCards]
    places: int
    complaint: str


REFUSED_PLACES: Final[tuple[RefusedPlacesCase, ...]] = (
    RefusedPlacesCase(
        description="one card is alike to nothing",
        pattern=SameRank,
        places=1,
        complaint="greater than or equal to 2",
    ),
    RefusedPlacesCase(
        description="one card holds no suit in common",
        pattern=SameSuit,
        places=1,
        complaint="greater than or equal to 2",
    ),
    RefusedPlacesCase(
        description="one card runs nowhere",
        pattern=Run,
        places=1,
        complaint="greater than or equal to 2",
    ),
    RefusedPlacesCase(
        description="a run reaches as far as the ranks stretch",
        pattern=Run,
        places=len(Rank) + 1,
        complaint="less than or equal to 13",
    ),
    RefusedPlacesCase(
        description="a pattern fills a place at the least",
        pattern=AnyCards,
        places=0,
        complaint="greater than or equal to 1",
    ),
)


@pytest.mark.parametrize("case", REFUSED_PLACES, ids=descriptions(REFUSED_PLACES))
def test_a_pattern_holds_the_places_its_rule_reaches(case: RefusedPlacesCase) -> None:
    with pytest.raises(ValidationError, match=case.complaint):
        case.pattern(places=case.places)


@dataclass(frozen=True)
class RefusedPartsCase(Case):
    pattern: type[Together] | type[Beside]
    parts: tuple[Pattern, ...]
    complaint: str


REFUSED_PARTS: Final[tuple[RefusedPartsCase, ...]] = (
    RefusedPartsCase(
        description="parts read together fill one set of places",
        pattern=Together,
        parts=(PAIR, TRIPLET),
        complaint=r"ask for \[2, 3\] places",
    ),
    RefusedPartsCase(
        description="reading together takes two parts",
        pattern=Together,
        parts=(PAIR,),
        complaint="at least 2 items",
    ),
    RefusedPartsCase(
        description="standing beside takes two parts",
        pattern=Beside,
        parts=(PAIR,),
        complaint="at least 2 items",
    ),
)


@pytest.mark.parametrize("case", REFUSED_PARTS, ids=descriptions(REFUSED_PARTS))
def test_a_pattern_made_of_parts_holds_them_to_its_rule(case: RefusedPartsCase) -> None:
    with pytest.raises(ValidationError, match=case.complaint):
        case.pattern(parts=case.parts)


def test_the_wheel_is_the_last_reading_of_a_run_and_the_only_one_running_low() -> None:
    admitted = tuple(STRAIGHT.shapes(REGULAR_EVALUATION))

    assert admitted[-1].demands == _ranks(*WHEEL)
    assert admitted[-1].low_ace is True
    assert [shape.low_ace for shape in admitted[:-1]] == [False] * (len(admitted) - 1)


def test_a_reading_that_leaves_the_wheel_out_stops_at_the_lowest_stretch() -> None:
    admitted = tuple(STRAIGHT.shapes(NO_WHEEL))

    assert len(admitted) == len(Rank) - POKER_HAND + 1
    assert admitted[-1].demands == _ranks(Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX)
    assert not any(shape.low_ace for shape in admitted)


def test_a_suited_run_carries_the_low_ace_of_the_run_it_reads_with() -> None:
    admitted = tuple(STRAIGHT_FLUSH.shapes(REGULAR_EVALUATION))
    low = tuple(shape for shape in admitted if shape.low_ace)

    assert len(low) == len(Suit)
    assert low[0].demands == _cards(Suit.SPADE, *WHEEL)


def test_parts_standing_beside_each_other_keep_their_own_ranks() -> None:
    admitted = tuple(FULL_HOUSE.shapes(REGULAR_EVALUATION))

    assert all(len(shape.ranks) == 2 for shape in admitted)
    assert len({shape.demands for shape in admitted}) == len(admitted)


def test_parts_reading_alike_are_counted_once() -> None:
    admitted = tuple(TWO_PAIR.shapes(REGULAR_EVALUATION))
    read = {frozenset(shape.ranks) for shape in admitted}

    assert len(read) == len(admitted)
    assert admitted[0].ranks == frozenset({Rank.ACE, Rank.KING})


def test_a_pattern_of_parts_reads_every_part_over_the_places_it_names() -> None:
    reading = (FIVE_OF_SPADES, FIVE_OF_HEARTS, FIVE_OF_CLUBS, ACE_OF_SPADES, ACE_OF_HEARTS)
    triplet, pair = FULL_HOUSE.strength(reading, REGULAR_EVALUATION)

    assert triplet == PLACES[Rank.FIVE]
    assert pair == PLACES[Rank.ACE]


def test_places_asked_for_two_suits_at_once_hold_no_reading() -> None:
    one_suit = Together(parts=(SameSuit(places=2), SameSuit(places=2)))

    admitted = tuple(one_suit.shapes(REGULAR_EVALUATION))

    assert len(admitted) == len(Suit)
    assert all(len(shape.suits) == 1 for shape in admitted)


def test_a_pattern_answers_the_evaluation_it_is_read_under() -> None:
    short = Evaluation(
        ranks=REGULAR_EVALUATION.ranks,
        suits=(Suit.CLUB, Suit.DIAMOND, Suit.HEART, Suit.SPADE),
        wheel=False,
        wild_jokers=False,
        duplicates=Duplicates.COLLAPSE,
    )

    assert len(tuple(STRAIGHT.shapes(short))) == len(Rank) - POKER_HAND + 1
    assert len(tuple(THREE_OF_A_SUIT.shapes(short))) == len(Suit)


def test_every_pattern_a_ranking_lists_admits_a_reading() -> None:
    listed = (
        HIGH_CARD,
        PAIR,
        TWO_PAIR,
        TRIPLET,
        STRAIGHT,
        FLUSH,
        FULL_HOUSE,
        QUADRUPLET,
        STRAIGHT_FLUSH,
        FIVE_OF_A_RANK,
        ONE_PAIR,
        SUITED_PAIR,
        LONGEST_RUN,
    )

    assert all(tuple(pattern.shapes(REGULAR_EVALUATION)) for pattern in listed)


def test_patterns_stating_one_rule_stand_as_one_pattern() -> None:
    assert SameRank(places=2) == PAIR
    assert Beside(parts=(TRIPLET, PAIR)) == FULL_HOUSE
    assert AnyCards(places=1) == HIGH_CARD
    assert SameRank(places=2) != SameSuit(places=2)
    assert len({SameRank(places=2), PAIR, SameSuit(places=2)}) == 2
