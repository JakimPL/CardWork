from collections.abc import Callable, Sequence
from dataclasses import dataclass
from itertools import combinations, product
from typing import Final

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from cardwork.cards.card import Card, Cards
from cardwork.cards.cards import (
    ACE_OF_CLUBS,
    ACE_OF_DIAMONDS,
    ACE_OF_HEARTS,
    ACE_OF_SPADES,
    BLACK_JOKER,
    FIVE_OF_SPADES,
    FOUR_OF_SPADES,
    KING_OF_CLUBS,
    KING_OF_DIAMONDS,
    KING_OF_HEARTS,
    KING_OF_SPADES,
    QUEEN_OF_DIAMONDS,
    QUEEN_OF_HEARTS,
    QUEEN_OF_SPADES,
    RED_JOKER,
    STANDARD_CARDS,
    THREE_OF_SPADES,
    TWO_OF_HEARTS,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardOrJoker, CardsOrJokers
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.combinations.detect import contains, find
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.patterns.any_cards import AnyCards
from cardwork.combinations.patterns.apart import Apart
from cardwork.combinations.patterns.beside import Beside
from cardwork.combinations.patterns.same_rank import SameRank
from cardwork.combinations.patterns.same_suit import SameSuit
from cardwork.combinations.patterns.together import Together
from cardwork.combinations.poker import (
    FLUSH,
    PAIR,
    QUADRUPLET,
    STRAIGHT,
    TRIPLET,
    TWO_PAIR,
)
from cardwork.combinations.policy import REGULAR_EVALUATION, Duplicates, Evaluation
from tests.cases import Case, descriptions

type Holds = Callable[[Cards], bool]

ORACLE_RANKS: Final[tuple[Rank, ...]] = (Rank.KING, Rank.QUEEN)
ORACLE_DECK: Final[Cards] = tuple(Card(rank=rank, suit=suit) for rank in ORACLE_RANKS for suit in Suit)
MOST_HELD: Final[int] = 5
PAIR_PLACES: Final[int] = 2
FIRST_PLACE: Final[int] = 0

COLLAPSING: Final[Evaluation] = Evaluation(
    ranks=REGULAR_EVALUATION.ranks,
    suits=REGULAR_EVALUATION.suits,
    wheel=True,
    wild_jokers=True,
    duplicates=Duplicates.COLLAPSE,
)
NO_JOKERS: Final[Evaluation] = Evaluation(
    ranks=REGULAR_EVALUATION.ranks,
    suits=REGULAR_EVALUATION.suits,
    wheel=True,
    wild_jokers=False,
    duplicates=Duplicates.COUNT,
)

FIVE_OF_A_RANK: Final[Pattern] = SameRank(places=5)
THREE_OF_A_SUIT: Final[Pattern] = SameSuit(places=3)
TWO_LOOSE: Final[Pattern] = AnyCards(places=2)
THREE_LOOSE: Final[Pattern] = AnyCards(places=3)
PAIR_WITH_A_KICKER: Final[Pattern] = Beside(parts=(PAIR, AnyCards(places=1)))
FULL_HOUSE: Final[Pattern] = Beside(parts=(TRIPLET, PAIR))
SUITED_PAIR: Final[Pattern] = Together(parts=(PAIR, SameSuit(places=2)))

APART_PAIR: Final[Pattern] = Apart.of_suit(PAIR)
APART_PAIR_BY_CARD: Final[Pattern] = Apart.of_card(PAIR)
APART_TRIPLET: Final[Pattern] = Apart.of_suit(TRIPLET)
APART_QUADRUPLET: Final[Pattern] = Apart.of_suit(QUADRUPLET)
APART_FIVE_OF_A_RANK: Final[Pattern] = Apart.of_suit(FIVE_OF_A_RANK)
APART_THREE_OF_A_SUIT: Final[Pattern] = Apart.of_rank(THREE_OF_A_SUIT)
APART_FLUSH: Final[Pattern] = Apart.of_rank(FLUSH)
APART_TWO_LOOSE: Final[Pattern] = Apart.of_card(TWO_LOOSE)
APART_THREE_LOOSE: Final[Pattern] = Apart.of_card(THREE_LOOSE)
APART_TWO_PAIR: Final[Pattern] = Apart.of_card(TWO_PAIR)
TWO_APART_PAIRS: Final[Pattern] = Beside(parts=(APART_PAIR, APART_PAIR))
APART_FULL_HOUSE: Final[Pattern] = Beside(parts=(APART_TRIPLET, APART_PAIR))
APART_PAIR_WITH_A_KICKER: Final[Pattern] = Beside(parts=(APART_PAIR, AnyCards(places=1)))
APART_SUITED_PAIR: Final[Pattern] = Apart.of_card(SUITED_PAIR)
APART_STRAIGHT: Final[Pattern] = Apart.of_card(STRAIGHT)


@dataclass(frozen=True)
class HoldingCase(Case):
    """One hand beside a rule read apart and the rule it reads, and whether each of them holds among it.

    The two answers together are what reading apart states: `plain` is what the hand comes to where every copy
    answers for itself, and `apart` is what it comes to where the places each take a facing of their own. A row
    where the two differ is a row a second deck made possible.
    """

    cards: CardsOrJokers
    apart: Pattern
    plain: Pattern
    held_apart: bool
    held_plain: bool


HOLDINGS: Final[tuple[HoldingCase, ...]] = (
    HoldingCase(
        description="a pair of two suits holds both ways",
        cards=(KING_OF_SPADES, KING_OF_HEARTS),
        apart=APART_PAIR,
        plain=PAIR,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="one card held twice is a pair and holds no pair of two suits",
        cards=(KING_OF_SPADES, KING_OF_SPADES),
        apart=APART_PAIR,
        plain=PAIR,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="a card held twice beside a third of its rank holds a pair of two suits",
        cards=(KING_OF_SPADES, KING_OF_SPADES, KING_OF_HEARTS),
        apart=APART_PAIR,
        plain=PAIR,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="a pair of two suits reads apart by card as well",
        cards=(KING_OF_SPADES, KING_OF_HEARTS),
        apart=APART_PAIR_BY_CARD,
        plain=PAIR,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="one card held twice reads apart by card no more than by suit",
        cards=(KING_OF_SPADES, KING_OF_SPADES),
        apart=APART_PAIR_BY_CARD,
        plain=PAIR,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="two cards of a rank held twice each hold a triplet and no triplet apart",
        cards=(KING_OF_SPADES, KING_OF_SPADES, KING_OF_HEARTS, KING_OF_HEARTS),
        apart=APART_TRIPLET,
        plain=TRIPLET,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="three suits of a rank hold a triplet apart",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_DIAMONDS),
        apart=APART_TRIPLET,
        plain=TRIPLET,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="a card held twice beside two more of its rank holds a triplet apart",
        cards=(KING_OF_SPADES, KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS),
        apart=APART_TRIPLET,
        plain=TRIPLET,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="four suits of a rank hold a quadruplet apart",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_DIAMONDS, KING_OF_CLUBS),
        apart=APART_QUADRUPLET,
        plain=QUADRUPLET,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="two decks reach five of a rank, and four suits reach no five apart",
        cards=(KING_OF_SPADES, KING_OF_SPADES, KING_OF_HEARTS, KING_OF_DIAMONDS, KING_OF_CLUBS),
        apart=APART_FIVE_OF_A_RANK,
        plain=FIVE_OF_A_RANK,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="a card held twice is three of a suit and no three of a suit apart by rank",
        cards=(TWO_OF_SPADES, TWO_OF_SPADES, THREE_OF_SPADES),
        apart=APART_THREE_OF_A_SUIT,
        plain=THREE_OF_A_SUIT,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="three ranks of a suit hold three of a suit apart by rank",
        cards=(TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES),
        apart=APART_THREE_OF_A_SUIT,
        plain=THREE_OF_A_SUIT,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="a flush of five ranks holds apart by rank",
        cards=(TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES, KING_OF_SPADES),
        apart=APART_FLUSH,
        plain=FLUSH,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="a flush leaning on a card held twice holds no flush apart by rank",
        cards=(TWO_OF_SPADES, TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES),
        apart=APART_FLUSH,
        plain=FLUSH,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="two loose places take any two cards, and apart by card they take two of them",
        cards=(KING_OF_SPADES, TWO_OF_HEARTS),
        apart=APART_TWO_LOOSE,
        plain=TWO_LOOSE,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="one card held twice fills two loose places and no two apart by card",
        cards=(KING_OF_SPADES, KING_OF_SPADES),
        apart=APART_TWO_LOOSE,
        plain=TWO_LOOSE,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="one card held twice beside a second card fills two loose places apart",
        cards=(KING_OF_SPADES, KING_OF_SPADES, TWO_OF_HEARTS),
        apart=APART_TWO_LOOSE,
        plain=TWO_LOOSE,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="two cards held twice each fill three loose places and two apart by card",
        cards=(KING_OF_SPADES, KING_OF_SPADES, TWO_OF_HEARTS, TWO_OF_HEARTS),
        apart=APART_THREE_LOOSE,
        plain=THREE_LOOSE,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="two pair of one suit hold apart by card, since two ranks hold them apart",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_SPADES, QUEEN_OF_HEARTS),
        apart=APART_TWO_PAIR,
        plain=TWO_PAIR,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="two cards each held twice are two pair and no two pair apart by card",
        cards=(KING_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES, QUEEN_OF_SPADES),
        apart=APART_TWO_PAIR,
        plain=TWO_PAIR,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="two pairs of two suits each hold two pairs read apart",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_SPADES, QUEEN_OF_HEARTS),
        apart=TWO_APART_PAIRS,
        plain=TWO_PAIR,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="a pair leaning on a card held twice leaves two pairs read apart short",
        cards=(KING_OF_SPADES, KING_OF_SPADES, QUEEN_OF_SPADES, QUEEN_OF_HEARTS),
        apart=TWO_APART_PAIRS,
        plain=TWO_PAIR,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="one suit across both pairs holds them apart, each pair holding its own two",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_SPADES, QUEEN_OF_DIAMONDS),
        apart=TWO_APART_PAIRS,
        plain=TWO_PAIR,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="a full house of three suits and two holds apart",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_DIAMONDS, QUEEN_OF_SPADES, QUEEN_OF_HEARTS),
        apart=APART_FULL_HOUSE,
        plain=FULL_HOUSE,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="a full house leaning on a card held twice leaves the triplet short",
        cards=(KING_OF_SPADES, KING_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_SPADES, QUEEN_OF_SPADES),
        apart=APART_FULL_HOUSE,
        plain=FULL_HOUSE,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="a kicker repeating a card of the pair stands, since the loose place reads apart in nothing",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_SPADES),
        apart=APART_PAIR_WITH_A_KICKER,
        plain=PAIR_WITH_A_KICKER,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="one card held three times holds a pair with a kicker and no pair apart",
        cards=(KING_OF_SPADES, KING_OF_SPADES, KING_OF_SPADES),
        apart=APART_PAIR_WITH_A_KICKER,
        plain=PAIR_WITH_A_KICKER,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="a suited pair asks one card of both places, so a second deck alone holds it",
        cards=(KING_OF_SPADES, KING_OF_SPADES),
        apart=APART_SUITED_PAIR,
        plain=SUITED_PAIR,
        held_apart=False,
        held_plain=True,
    ),
    HoldingCase(
        description="a run holds ranks of its own, so reading it apart by card asks nothing more",
        cards=(TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES, ACE_OF_SPADES),
        apart=APART_STRAIGHT,
        plain=STRAIGHT,
        held_apart=True,
        held_plain=True,
    ),
    HoldingCase(
        description="a run leaning on a card held twice runs no further either way",
        cards=(TWO_OF_SPADES, TWO_OF_SPADES, THREE_OF_SPADES, FOUR_OF_SPADES, FIVE_OF_SPADES),
        apart=APART_STRAIGHT,
        plain=STRAIGHT,
        held_apart=False,
        held_plain=False,
    ),
)


@pytest.mark.parametrize("case", HOLDINGS, ids=descriptions(HOLDINGS))
def test_a_hand_answers_a_rule_read_apart_where_its_places_take_facings_of_their_own(case: HoldingCase) -> None:
    assert contains(case.cards, case.apart, REGULAR_EVALUATION) is case.held_apart
    assert contains(case.cards, case.plain, REGULAR_EVALUATION) is case.held_plain


@pytest.mark.parametrize("case", HOLDINGS, ids=descriptions(HOLDINGS))
def test_a_reading_collapsing_repeats_answers_a_rule_read_apart_as_the_rule_it_reads(case: HoldingCase) -> None:
    """A reading that drops repeats leaves a rule read apart asking what the rule it reads asks.

    The two statements meet where every card of a hand reads once: every card then faces apart from every other,
    so a spread turns nothing away. They part where a hand holds a card twice, which is the whole of what
    reading places apart is for.
    """
    assert contains(case.cards, case.apart, COLLAPSING) is contains(case.cards, case.plain, COLLAPSING)


@dataclass(frozen=True)
class ReadingCase(Case):
    """One hand beside the cards a rule read apart holds of it and what each of those cards reads as."""

    cards: CardsOrJokers
    pattern: Pattern
    held: CardsOrJokers
    reading: Cards


READINGS: Final[tuple[ReadingCase, ...]] = (
    ReadingCase(
        description="a joker beside one card reads as the strongest suit the pair leaves free",
        cards=(KING_OF_SPADES, RED_JOKER),
        pattern=APART_PAIR,
        held=(KING_OF_SPADES, RED_JOKER),
        reading=(KING_OF_SPADES, KING_OF_HEARTS),
    ),
    ReadingCase(
        description="two jokers read as two suits of one rank, the strongest first",
        cards=(RED_JOKER, BLACK_JOKER),
        pattern=APART_PAIR,
        held=(RED_JOKER, BLACK_JOKER),
        reading=(ACE_OF_SPADES, ACE_OF_HEARTS),
    ),
    ReadingCase(
        description="a card held twice beside a joker leaves the joker the suits the one copy leaves",
        cards=(KING_OF_SPADES, KING_OF_SPADES, RED_JOKER),
        pattern=APART_PAIR,
        held=(KING_OF_SPADES, RED_JOKER),
        reading=(KING_OF_SPADES, KING_OF_HEARTS),
    ),
    ReadingCase(
        description="three jokers read as three suits of the strongest rank",
        cards=(RED_JOKER, BLACK_JOKER, RED_JOKER),
        pattern=APART_TRIPLET,
        held=(RED_JOKER, BLACK_JOKER, RED_JOKER),
        reading=(ACE_OF_SPADES, ACE_OF_HEARTS, ACE_OF_DIAMONDS),
    ),
    ReadingCase(
        description="four suits of a rank leave four jokers reading a quadruplet apart",
        cards=(RED_JOKER, RED_JOKER, BLACK_JOKER, BLACK_JOKER),
        pattern=APART_QUADRUPLET,
        held=(RED_JOKER, RED_JOKER, BLACK_JOKER, BLACK_JOKER),
        reading=(ACE_OF_SPADES, ACE_OF_HEARTS, ACE_OF_DIAMONDS, ACE_OF_CLUBS),
    ),
    ReadingCase(
        description="a joker in a flush read apart by rank leaves the ranks the suit already shows",
        cards=(TWO_OF_SPADES, THREE_OF_SPADES, RED_JOKER),
        pattern=APART_THREE_OF_A_SUIT,
        held=(THREE_OF_SPADES, TWO_OF_SPADES, RED_JOKER),
        reading=(THREE_OF_SPADES, TWO_OF_SPADES, ACE_OF_SPADES),
    ),
    ReadingCase(
        description="a joker fills the pair the second copy of a card cannot",
        cards=(QUEEN_OF_SPADES, QUEEN_OF_HEARTS, KING_OF_SPADES, KING_OF_SPADES, RED_JOKER),
        pattern=TWO_APART_PAIRS,
        held=(KING_OF_SPADES, RED_JOKER, QUEEN_OF_SPADES, QUEEN_OF_HEARTS),
        reading=(KING_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_SPADES, QUEEN_OF_HEARTS),
    ),
)


@pytest.mark.parametrize("case", READINGS, ids=descriptions(READINGS))
def test_a_rule_read_apart_reads_a_joker_as_a_facing_its_spread_leaves_free(case: ReadingCase) -> None:
    found = find(case.cards, case.pattern, REGULAR_EVALUATION)

    assert found is not None
    assert found.cards == case.held
    assert found.reading == case.reading


@dataclass(frozen=True)
class ShortCase(Case):
    """One rule read apart that a hand falls short of however many jokers stand behind it."""

    cards: CardsOrJokers
    pattern: Pattern


FALLING_SHORT: Final[tuple[ShortCase, ...]] = (
    ShortCase(
        description="five places apart by suit reach past the four suits a deck holds",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_DIAMONDS, KING_OF_CLUBS, RED_JOKER, RED_JOKER),
        pattern=APART_FIVE_OF_A_RANK,
    ),
    ShortCase(
        description="jokers to spare reach no fifth suit either",
        cards=(RED_JOKER, RED_JOKER, RED_JOKER, RED_JOKER, RED_JOKER, RED_JOKER),
        pattern=APART_FIVE_OF_A_RANK,
    ),
    ShortCase(
        description="a suited pair asks one card of two places, which reading them apart leaves nowhere",
        cards=(RED_JOKER, RED_JOKER, KING_OF_SPADES, KING_OF_SPADES),
        pattern=APART_SUITED_PAIR,
    ),
)


@pytest.mark.parametrize("case", FALLING_SHORT, ids=descriptions(FALLING_SHORT))
def test_a_spread_reaching_past_the_facings_a_deck_holds_admits_no_reading(case: ShortCase) -> None:
    assert contains(case.cards, case.pattern, REGULAR_EVALUATION) is False
    assert find(case.cards, case.pattern, REGULAR_EVALUATION) is None


def test_a_rule_read_apart_holds_of_one_deck_what_the_rule_it_reads_holds() -> None:
    """Over a deck holding every card once, reading places apart by card asks nothing the rule does not.

    Every card of such a hand faces apart from every other, so the spread turns nothing away, and the two rules
    answer alike for every hand a single deck deals.
    """
    hand = (KING_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_SPADES, QUEEN_OF_HEARTS, TWO_OF_SPADES, THREE_OF_SPADES)
    listed = (PAIR, TRIPLET, TWO_PAIR, THREE_OF_A_SUIT, TWO_LOOSE, THREE_LOOSE, PAIR_WITH_A_KICKER)

    for pattern in listed:
        held = contains(hand, pattern, NO_JOKERS)
        assert contains(hand, Apart.of_card(pattern), NO_JOKERS) is held


def _alike_apart(reading: Cards, facing: Callable[[Card], object]) -> bool:
    """Whether every card of the reading shows a facing of its own."""
    shown = [facing(card) for card in reading]
    return len(set(shown)) == len(shown)


def _one_rank(reading: Cards) -> bool:
    return len({card.rank for card in reading}) == 1


def _two_pairs_apart(reading: Cards) -> bool:
    """Whether the reading splits into two pairs of different ranks, each pair showing two suits."""
    places = range(len(reading))
    for taken in combinations(places, PAIR_PLACES):
        pair = tuple(reading[place] for place in taken)
        rest = tuple(reading[place] for place in places if place not in taken)
        if len(rest) != PAIR_PLACES:
            continue

        if (
            _one_rank(pair)
            and _one_rank(rest)
            and pair[FIRST_PLACE].rank != rest[FIRST_PLACE].rank
            and _alike_apart(pair, lambda card: card.suit)
            and _alike_apart(rest, lambda card: card.suit)
        ):
            return True

    return False


@dataclass(frozen=True)
class RuleCase(Case):
    """One rule read apart beside a statement of what it asks, written from the rule rather than the search.

    The statement answers for a run of cards directly, which is the reference the filling is held against: it
    says what a reading of the rule is and leaves finding one alone.
    """

    pattern: Pattern
    places: int
    holds: Holds


RULES: Final[tuple[RuleCase, ...]] = (
    RuleCase(
        description="a pair apart by suit is two cards of one rank showing two suits",
        pattern=APART_PAIR,
        places=2,
        holds=lambda reading: _one_rank(reading) and _alike_apart(reading, lambda card: card.suit),
    ),
    RuleCase(
        description="a pair apart by card is two cards of one rank, neither of them the other",
        pattern=APART_PAIR_BY_CARD,
        places=2,
        holds=lambda reading: _one_rank(reading) and _alike_apart(reading, lambda card: card),
    ),
    RuleCase(
        description="a triplet apart by suit is three cards of one rank showing three suits",
        pattern=APART_TRIPLET,
        places=3,
        holds=lambda reading: _one_rank(reading) and _alike_apart(reading, lambda card: card.suit),
    ),
    RuleCase(
        description="a quadruplet apart by suit is four cards of one rank showing four suits",
        pattern=APART_QUADRUPLET,
        places=4,
        holds=lambda reading: _one_rank(reading) and _alike_apart(reading, lambda card: card.suit),
    ),
    RuleCase(
        description="two loose places apart by card are two cards, neither of them the other",
        pattern=APART_TWO_LOOSE,
        places=2,
        holds=lambda reading: _alike_apart(reading, lambda card: card),
    ),
    RuleCase(
        description="three loose places apart by card are three cards, no two of them alike",
        pattern=APART_THREE_LOOSE,
        places=3,
        holds=lambda reading: _alike_apart(reading, lambda card: card),
    ),
    RuleCase(
        description="two pair apart by card are two pairs of two ranks, no card of them twice",
        pattern=APART_TWO_PAIR,
        places=4,
        holds=lambda reading: _two_pairs_apart(reading) and _alike_apart(reading, lambda card: card),
    ),
    RuleCase(
        description="two pairs read apart are a pair of two suits beside another of two suits",
        pattern=TWO_APART_PAIRS,
        places=4,
        holds=_two_pairs_apart,
    ),
)


def _readings(held: Sequence[CardOrJoker], places: int) -> list[Cards]:
    """Every reading these cards make over that many places, a joker standing for any card of the deck."""
    made: list[Cards] = []
    for taken in combinations(range(len(held)), places):
        naturals = tuple(card for card in (held[place] for place in taken) if isinstance(card, Card))
        for stood in product(STANDARD_CARDS, repeat=places - len(naturals)):
            made.append((*naturals, *stood))

    return made


def _found(held: Sequence[CardOrJoker], case: RuleCase) -> bool:
    """Whether the cards make any reading the rule holds of, found by trying every reading they make."""
    return any(case.holds(reading) for reading in _readings(held, case.places))


@st.composite
def _hands(draw: st.DrawFn) -> CardsOrJokers:
    """A hand of two ranks over four suits, cards repeating as a second deck lets them, and a joker besides."""
    held = draw(st.lists(st.sampled_from(ORACLE_DECK), max_size=MOST_HELD))
    wild = draw(st.booleans())
    return (*held, RED_JOKER) if wild else tuple(held)


@pytest.mark.parametrize("case", RULES, ids=descriptions(RULES))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow], max_examples=150)
@given(hand=_hands())
def test_the_filling_holds_a_rule_read_apart_of_the_hands_the_rule_itself_holds_of(
    case: RuleCase,
    hand: CardsOrJokers,
) -> None:
    assert contains(hand, case.pattern, REGULAR_EVALUATION) is _found(hand, case)
