from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.cards.card import Card
from cardwork.cards.cards import (
    ACE_OF_CLUBS,
    ACE_OF_DIAMONDS,
    ACE_OF_HEARTS,
    ACE_OF_SPADES,
    BLACK_JOKER,
    FIVE_OF_DIAMONDS,
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    FOUR_OF_CLUBS,
    FOUR_OF_DIAMONDS,
    FOUR_OF_SPADES,
    JACK_OF_SPADES,
    KING_OF_CLUBS,
    KING_OF_DIAMONDS,
    KING_OF_HEARTS,
    KING_OF_SPADES,
    NINE_OF_DIAMONDS,
    NINE_OF_HEARTS,
    NINE_OF_SPADES,
    QUEEN_OF_SPADES,
    RED_JOKER,
    SEVEN_OF_DIAMONDS,
    SEVEN_OF_HEARTS,
    SEVEN_OF_SPADES,
    SIX_OF_HEARTS,
    SIX_OF_SPADES,
    THREE_OF_CLUBS,
    THREE_OF_HEARTS,
    THREE_OF_SPADES,
    TWO_OF_CLUBS,
    TWO_OF_DIAMONDS,
    TWO_OF_HEARTS,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardOrJoker
from cardwork.combinations.detect import contains, find, find_all, matches
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.patterns.any_cards import AnyCards
from cardwork.combinations.patterns.beside import Beside
from cardwork.combinations.patterns.run import Run
from cardwork.combinations.patterns.same_suit import SameSuit
from cardwork.combinations.poker import (
    FULL_HOUSE,
    HIGH_CARD,
    PAIR,
    QUADRUPLET,
    STRAIGHT,
    STRAIGHT_FLUSH,
    TRIPLET,
    TWO_PAIR,
)
from cardwork.combinations.policy import REGULAR_EVALUATION, Duplicates, Evaluation
from tests.cases import Case, descriptions

COLLAPSING: Final[Evaluation] = Evaluation(
    ranks=REGULAR_EVALUATION.ranks,
    suits=REGULAR_EVALUATION.suits,
    wheel=True,
    wild_jokers=True,
    duplicates=Duplicates.COLLAPSE,
)
NO_WHEEL: Final[Evaluation] = Evaluation(
    ranks=REGULAR_EVALUATION.ranks,
    suits=REGULAR_EVALUATION.suits,
    wheel=False,
    wild_jokers=True,
    duplicates=Duplicates.COUNT,
)
TAME_JOKERS: Final[Evaluation] = Evaluation(
    ranks=REGULAR_EVALUATION.ranks,
    suits=REGULAR_EVALUATION.suits,
    wheel=True,
    wild_jokers=False,
    duplicates=Duplicates.COUNT,
)
THREE_OF_A_SUIT: Final[Pattern] = SameSuit(places=3)
FOUR_OF_A_SUIT: Final[Pattern] = SameSuit(places=4)
THREE_IN_A_ROW: Final[Pattern] = Run(places=3)
PAIR_BESIDE_THREE_OF_A_SUIT: Final[Pattern] = Beside(parts=(PAIR, THREE_OF_A_SUIT))
PAIR_BESIDE_LOOSE_CARDS: Final[Pattern] = Beside(parts=(PAIR, AnyCards(places=3)))


@dataclass(frozen=True)
class ReadingCase(Case):
    cards: tuple[CardOrJoker, ...]
    pattern: Pattern
    holds: bool
    is_all_of_it: bool
    reading: tuple[Card, ...] | None


READINGS: Final[tuple[ReadingCase, ...]] = (
    ReadingCase(
        description="three sevens are a triplet, and all of one",
        cards=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS),
        pattern=TRIPLET,
        holds=True,
        is_all_of_it=True,
        reading=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS),
    ),
    ReadingCase(
        description="three sevens beside an odd card hold a triplet",
        cards=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS, TWO_OF_CLUBS),
        pattern=TRIPLET,
        holds=True,
        is_all_of_it=False,
        reading=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS),
    ),
    ReadingCase(
        description="two sevens fall short of a triplet",
        cards=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, TWO_OF_CLUBS),
        pattern=TRIPLET,
        holds=False,
        is_all_of_it=False,
        reading=None,
    ),
    ReadingCase(
        description="a joker stands in for the third seven",
        cards=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, RED_JOKER),
        pattern=TRIPLET,
        holds=True,
        is_all_of_it=True,
        reading=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS),
    ),
    ReadingCase(
        description="two jokers make a triplet of the highest rank held",
        cards=(NINE_OF_HEARTS, RED_JOKER, BLACK_JOKER),
        pattern=TRIPLET,
        holds=True,
        is_all_of_it=True,
        reading=(NINE_OF_HEARTS, NINE_OF_SPADES, NINE_OF_DIAMONDS),
    ),
    ReadingCase(
        description="three jokers make a triplet of aces",
        cards=(RED_JOKER, BLACK_JOKER, RED_JOKER),
        pattern=TRIPLET,
        holds=True,
        is_all_of_it=True,
        reading=(ACE_OF_SPADES, ACE_OF_HEARTS, ACE_OF_DIAMONDS),
    ),
    ReadingCase(
        description="two kings beside two jokers are a quadruplet",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, RED_JOKER, BLACK_JOKER),
        pattern=QUADRUPLET,
        holds=True,
        is_all_of_it=True,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_DIAMONDS, KING_OF_CLUBS),
    ),
    ReadingCase(
        description="three spades beside a heart hold three of a suit",
        cards=(KING_OF_SPADES, NINE_OF_SPADES, TWO_OF_SPADES, THREE_OF_HEARTS),
        pattern=THREE_OF_A_SUIT,
        holds=True,
        is_all_of_it=False,
        reading=(KING_OF_SPADES, NINE_OF_SPADES, TWO_OF_SPADES),
    ),
    ReadingCase(
        description="two spades and two hearts hold no three of a suit",
        cards=(KING_OF_SPADES, NINE_OF_SPADES, TWO_OF_HEARTS, THREE_OF_HEARTS),
        pattern=THREE_OF_A_SUIT,
        holds=False,
        is_all_of_it=False,
        reading=None,
    ),
    ReadingCase(
        description="four spades are four of a suit, and all of it",
        cards=(KING_OF_SPADES, NINE_OF_SPADES, THREE_OF_SPADES, TWO_OF_SPADES),
        pattern=FOUR_OF_A_SUIT,
        holds=True,
        is_all_of_it=True,
        reading=(KING_OF_SPADES, NINE_OF_SPADES, THREE_OF_SPADES, TWO_OF_SPADES),
    ),
    ReadingCase(
        description="a run of five in mixed suits is a straight",
        cards=(TWO_OF_SPADES, THREE_OF_HEARTS, FOUR_OF_CLUBS, FIVE_OF_DIAMONDS, SIX_OF_SPADES),
        pattern=STRAIGHT,
        holds=True,
        is_all_of_it=True,
        reading=(TWO_OF_SPADES, THREE_OF_HEARTS, FOUR_OF_CLUBS, FIVE_OF_DIAMONDS, SIX_OF_SPADES),
    ),
    ReadingCase(
        description="the ace runs low in A 2 3 4 5",
        cards=(ACE_OF_SPADES, TWO_OF_HEARTS, THREE_OF_CLUBS, FOUR_OF_DIAMONDS, FIVE_OF_SPADES),
        pattern=STRAIGHT,
        holds=True,
        is_all_of_it=True,
        reading=(ACE_OF_SPADES, TWO_OF_HEARTS, THREE_OF_CLUBS, FOUR_OF_DIAMONDS, FIVE_OF_SPADES),
    ),
    ReadingCase(
        description="a joker fills the gap in a run",
        cards=(TWO_OF_SPADES, THREE_OF_HEARTS, FIVE_OF_DIAMONDS, SIX_OF_SPADES, RED_JOKER),
        pattern=STRAIGHT,
        holds=True,
        is_all_of_it=True,
        reading=(TWO_OF_SPADES, THREE_OF_HEARTS, FOUR_OF_SPADES, FIVE_OF_DIAMONDS, SIX_OF_SPADES),
    ),
    ReadingCase(
        description="a repeated rank leaves a run one rank short",
        cards=(TWO_OF_SPADES, TWO_OF_HEARTS, THREE_OF_CLUBS, FOUR_OF_DIAMONDS, FIVE_OF_SPADES),
        pattern=STRAIGHT,
        holds=False,
        is_all_of_it=False,
        reading=None,
    ),
    ReadingCase(
        description="five spades in a row are a straight flush",
        cards=(TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES, SIX_OF_SPADES),
        pattern=STRAIGHT_FLUSH,
        holds=True,
        is_all_of_it=True,
        reading=(TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES, SIX_OF_SPADES),
    ),
    ReadingCase(
        description="a run across two suits is no straight flush",
        cards=(TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES, SIX_OF_HEARTS),
        pattern=STRAIGHT_FLUSH,
        holds=False,
        is_all_of_it=False,
        reading=None,
    ),
    ReadingCase(
        description="three kings beside two fives are a full house",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS, FIVE_OF_SPADES, FIVE_OF_HEARTS),
        pattern=FULL_HOUSE,
        holds=True,
        is_all_of_it=True,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS, FIVE_OF_SPADES, FIVE_OF_HEARTS),
    ),
    ReadingCase(
        description="four kings beside a fifth card are no full house",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS, KING_OF_DIAMONDS, FIVE_OF_SPADES),
        pattern=FULL_HOUSE,
        holds=False,
        is_all_of_it=False,
        reading=None,
    ),
    ReadingCase(
        description="two kings beside two fives are two pair",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, FIVE_OF_SPADES, FIVE_OF_HEARTS),
        pattern=TWO_PAIR,
        holds=True,
        is_all_of_it=True,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, FIVE_OF_SPADES, FIVE_OF_HEARTS),
    ),
    ReadingCase(
        description="four kings are one rank and so no two pair",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS, KING_OF_DIAMONDS),
        pattern=TWO_PAIR,
        holds=False,
        is_all_of_it=False,
        reading=None,
    ),
    ReadingCase(
        description="the strongest of two cards is the single they hold",
        cards=(SEVEN_OF_SPADES, TWO_OF_HEARTS),
        pattern=HIGH_CARD,
        holds=True,
        is_all_of_it=False,
        reading=(SEVEN_OF_SPADES,),
    ),
    ReadingCase(
        description="a joker alone reads as the ace of spades",
        cards=(RED_JOKER,),
        pattern=HIGH_CARD,
        holds=True,
        is_all_of_it=True,
        reading=(ACE_OF_SPADES,),
    ),
    ReadingCase(
        description="no cards hold nothing",
        cards=(),
        pattern=HIGH_CARD,
        holds=False,
        is_all_of_it=False,
        reading=None,
    ),
)


@pytest.mark.parametrize("case", READINGS, ids=descriptions(READINGS))
def test_a_pattern_reads_the_cards_that_hold_it(case: ReadingCase) -> None:
    found = find(case.cards, case.pattern, REGULAR_EVALUATION)

    assert contains(case.cards, case.pattern, REGULAR_EVALUATION) is case.holds
    assert matches(case.cards, case.pattern, REGULAR_EVALUATION) is case.is_all_of_it
    assert (found.reading if found is not None else None) == case.reading


@dataclass(frozen=True)
class DuplicatesCase(Case):
    cards: tuple[CardOrJoker, ...]
    pattern: Pattern
    counted: bool
    collapsed: bool


DUPLICATES: Final[tuple[DuplicatesCase, ...]] = (
    DuplicatesCase(
        description="one card held twice is a pair where copies count",
        cards=(TWO_OF_DIAMONDS, TWO_OF_DIAMONDS),
        pattern=PAIR,
        counted=True,
        collapsed=False,
    ),
    DuplicatesCase(
        description="two diamonds and a copy are three of a suit where copies count",
        cards=(TWO_OF_DIAMONDS, TWO_OF_DIAMONDS, THREE_OF_HEARTS, FOUR_OF_DIAMONDS),
        pattern=THREE_OF_A_SUIT,
        counted=True,
        collapsed=False,
    ),
    DuplicatesCase(
        description="three distinct spades read the same either way",
        cards=(TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES),
        pattern=THREE_OF_A_SUIT,
        counted=True,
        collapsed=True,
    ),
    DuplicatesCase(
        description="two cards of one rank are a pair either way",
        cards=(TWO_OF_DIAMONDS, TWO_OF_SPADES),
        pattern=PAIR,
        counted=True,
        collapsed=True,
    ),
    DuplicatesCase(
        description="a copy lengthens no run",
        cards=(TWO_OF_SPADES, TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES),
        pattern=STRAIGHT,
        counted=False,
        collapsed=False,
    ),
)


@pytest.mark.parametrize("case", DUPLICATES, ids=descriptions(DUPLICATES))
def test_a_reading_states_what_a_repeated_card_counts_for(case: DuplicatesCase) -> None:
    assert contains(case.cards, case.pattern, REGULAR_EVALUATION) is case.counted
    assert contains(case.cards, case.pattern, COLLAPSING) is case.collapsed


@dataclass(frozen=True)
class WheelCase(Case):
    cards: tuple[CardOrJoker, ...]
    pattern: Pattern
    admitted: bool
    without_the_wheel: bool


WHEELS: Final[tuple[WheelCase, ...]] = (
    WheelCase(
        description="A 2 3 4 5 runs where the wheel is admitted",
        cards=(ACE_OF_SPADES, TWO_OF_HEARTS, THREE_OF_CLUBS, FOUR_OF_DIAMONDS, FIVE_OF_SPADES),
        pattern=STRAIGHT,
        admitted=True,
        without_the_wheel=False,
    ),
    WheelCase(
        description="A 2 3 runs likewise over three cards",
        cards=(ACE_OF_SPADES, TWO_OF_HEARTS, THREE_OF_CLUBS),
        pattern=THREE_IN_A_ROW,
        admitted=True,
        without_the_wheel=False,
    ),
    WheelCase(
        description="a run up to the ace stands either way",
        cards=(QUEEN_OF_SPADES, KING_OF_HEARTS, ACE_OF_CLUBS),
        pattern=THREE_IN_A_ROW,
        admitted=True,
        without_the_wheel=True,
    ),
    WheelCase(
        description="K A 2 turns no corner",
        cards=(KING_OF_SPADES, ACE_OF_HEARTS, TWO_OF_CLUBS),
        pattern=THREE_IN_A_ROW,
        admitted=False,
        without_the_wheel=False,
    ),
)


@pytest.mark.parametrize("case", WHEELS, ids=descriptions(WHEELS))
def test_the_wheel_runs_where_a_reading_admits_it(case: WheelCase) -> None:
    assert contains(case.cards, case.pattern, REGULAR_EVALUATION) is case.admitted
    assert contains(case.cards, case.pattern, NO_WHEEL) is case.without_the_wheel


@dataclass(frozen=True)
class JokerCase(Case):
    cards: tuple[CardOrJoker, ...]
    pattern: Pattern
    wild: bool
    tame: bool


JOKERS: Final[tuple[JokerCase, ...]] = (
    JokerCase(
        description="a joker completes a triplet only where jokers are wild",
        cards=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, RED_JOKER),
        pattern=TRIPLET,
        wild=True,
        tame=False,
    ),
    JokerCase(
        description="a joker completes a flush only where jokers are wild",
        cards=(KING_OF_SPADES, NINE_OF_SPADES, BLACK_JOKER),
        pattern=THREE_OF_A_SUIT,
        wild=True,
        tame=False,
    ),
    JokerCase(
        description="natural cards read the same beside a tame joker",
        cards=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS, RED_JOKER),
        pattern=TRIPLET,
        wild=True,
        tame=True,
    ),
)


@pytest.mark.parametrize("case", JOKERS, ids=descriptions(JOKERS))
def test_a_reading_states_whether_a_joker_stands_in(case: JokerCase) -> None:
    assert contains(case.cards, case.pattern, REGULAR_EVALUATION) is case.wild
    assert contains(case.cards, case.pattern, TAME_JOKERS) is case.tame


def test_a_rank_yields_one_instance_however_many_cards_hold_it() -> None:
    three_kings = (KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS)

    found = find_all(three_kings, PAIR, REGULAR_EVALUATION)

    assert len(found) == 1
    assert found[0].reading == (KING_OF_SPADES, KING_OF_HEARTS)


def test_every_instance_comes_out_from_the_strongest_downwards() -> None:
    two_pairs = (FIVE_OF_HEARTS, KING_OF_SPADES, FIVE_OF_SPADES, KING_OF_HEARTS)

    found = find_all(two_pairs, PAIR, REGULAR_EVALUATION)

    assert [instance.reading for instance in found] == [
        (KING_OF_SPADES, KING_OF_HEARTS),
        (FIVE_OF_SPADES, FIVE_OF_HEARTS),
    ]


def test_two_jokers_hold_a_pair_of_every_rank() -> None:
    found = find_all((RED_JOKER, BLACK_JOKER), PAIR, REGULAR_EVALUATION)

    assert len(found) == len(REGULAR_EVALUATION.ranks)
    assert found[0].reading == (ACE_OF_SPADES, ACE_OF_HEARTS)


def test_a_hand_reads_as_every_pattern_it_forms() -> None:
    spades_in_a_row = (TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES, SIX_OF_SPADES)

    assert matches(spades_in_a_row, STRAIGHT_FLUSH, REGULAR_EVALUATION)
    assert matches(spades_in_a_row, STRAIGHT, REGULAR_EVALUATION)
    assert contains(spades_in_a_row, THREE_OF_A_SUIT, REGULAR_EVALUATION)


def test_a_flush_deeper_than_a_suit_names_its_strongest_card_again() -> None:
    all_wild = (RED_JOKER,) * (len(REGULAR_EVALUATION.ranks) + 1)

    found = find(all_wild, SameSuit(places=len(all_wild)), REGULAR_EVALUATION)

    assert found is not None
    assert found.reading[0] == ACE_OF_SPADES
    assert found.reading[-1] == ACE_OF_SPADES
    assert len(set(found.reading)) == len(REGULAR_EVALUATION.ranks)


def test_a_card_gives_up_its_place_so_that_another_part_may_hold_one() -> None:
    three_kings = (KING_OF_SPADES, KING_OF_HEARTS, KING_OF_DIAMONDS, QUEEN_OF_SPADES, JACK_OF_SPADES)

    found = find(three_kings, PAIR_BESIDE_THREE_OF_A_SUIT, REGULAR_EVALUATION)

    assert found is not None
    assert found.reading == (
        KING_OF_DIAMONDS,
        KING_OF_HEARTS,
        KING_OF_SPADES,
        QUEEN_OF_SPADES,
        JACK_OF_SPADES,
    )
    assert matches(three_kings, PAIR_BESIDE_THREE_OF_A_SUIT, REGULAR_EVALUATION)


def test_loose_places_take_the_strongest_cards_the_named_places_leave() -> None:
    kings_and_kickers = (KING_OF_SPADES, KING_OF_HEARTS, NINE_OF_HEARTS, SEVEN_OF_DIAMONDS, TWO_OF_CLUBS)

    found = find(kings_and_kickers, PAIR_BESIDE_LOOSE_CARDS, REGULAR_EVALUATION)

    assert found is not None
    assert found.reading == (
        KING_OF_SPADES,
        KING_OF_HEARTS,
        NINE_OF_HEARTS,
        SEVEN_OF_DIAMONDS,
        TWO_OF_CLUBS,
    )


def test_a_joker_takes_a_place_from_a_card_only_where_it_reads_stronger() -> None:
    low_spades = (TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, RED_JOKER, BLACK_JOKER)
    two_kings = (KING_OF_SPADES, KING_OF_HEARTS, RED_JOKER)

    reaching = find(low_spades, THREE_OF_A_SUIT, REGULAR_EVALUATION)
    standing = find(two_kings, PAIR, REGULAR_EVALUATION)

    assert reaching is not None
    assert reaching.cards == (FOUR_OF_SPADES, RED_JOKER, BLACK_JOKER)
    assert reaching.reading == (FOUR_OF_SPADES, ACE_OF_SPADES, KING_OF_SPADES)
    assert standing is not None
    assert standing.cards == (KING_OF_SPADES, KING_OF_HEARTS)


def test_a_joker_takes_the_place_the_reading_gives_it() -> None:
    found = find((TWO_OF_SPADES, THREE_OF_HEARTS, RED_JOKER), THREE_IN_A_ROW, REGULAR_EVALUATION)

    assert found is not None
    assert found.cards == (TWO_OF_SPADES, THREE_OF_HEARTS, RED_JOKER)
    assert found.reading == (TWO_OF_SPADES, THREE_OF_HEARTS, FOUR_OF_SPADES)
    assert found.low_ace is False
