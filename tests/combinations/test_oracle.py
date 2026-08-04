from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from itertools import combinations, product
from typing import Final

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from cardwork.cards.card import Card
from cardwork.cards.cards import BLACK_JOKER, RED_JOKER, STANDARD_CARDS
from cardwork.cards.game import CardOrJoker
from cardwork.cards.joker import Joker
from cardwork.cards.orders import RANK_SEQUENCE
from cardwork.cards.suit import Suit
from cardwork.combinations.detect import contains, matches
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.patterns.any_cards import AnyCards
from cardwork.combinations.patterns.beside import Beside
from cardwork.combinations.patterns.run import Run
from cardwork.combinations.patterns.same_rank import SameRank
from cardwork.combinations.patterns.same_suit import SameSuit
from cardwork.combinations.patterns.together import Together
from cardwork.combinations.poker import (
    FULL_HOUSE,
    PAIR,
    QUADRUPLET,
    STRAIGHT,
    TRIPLET,
    TWO_PAIR,
    WHEEL,
)
from cardwork.combinations.policy import REGULAR_EVALUATION
from tests.cases import Case

PAIR_CARDS: Final[int] = 2
TRIPLET_CARDS: Final[int] = 3
SHORT_RUN: Final[int] = 3
POKER_HAND: Final[int] = 5
SHORT_HAND: Final[int] = 4

CLOSE_SUITS: Final[frozenset[Suit]] = frozenset({Suit.SPADE, Suit.HEART, Suit.CLUB})
SMALL_DECK: Final[tuple[Card, ...]] = tuple(
    card for card in STANDARD_CARDS if card.rank in WHEEL and card.suit in CLOSE_SUITS
)
JOKERS: Final[tuple[Joker, ...]] = (BLACK_JOKER, RED_JOKER)


def _alike(cards: Sequence[Card], places: int) -> bool:
    """Whether these are that many cards of one rank."""
    return len(cards) == places and len({card.rank for card in cards}) == 1


def _suited(cards: Sequence[Card], places: int) -> bool:
    """Whether these are that many cards of one suit."""
    return len(cards) == places and len({card.suit for card in cards}) == 1


def _shared(cards: Sequence[Card], shares: list[int]) -> bool:
    """Whether the ranks of these cards are held in shares of those sizes."""
    return sorted(Counter(card.rank for card in cards).values()) == shares


def _in_a_row(cards: Sequence[Card]) -> bool:
    """Whether these ranks are consecutive, counting a stretch turning at the ace as one of its own."""
    places = sorted(RANK_SEQUENCE.index(card.rank) for card in cards)
    if len(set(places)) != len(places):
        return False

    if places == list(range(places[0], places[0] + len(places))):
        return True

    return places == [*range(len(places) - 1), len(RANK_SEQUENCE) - 1]


def _run(cards: Sequence[Card], places: int) -> bool:
    """Whether these are that many cards in a row."""
    return len(cards) == places and _in_a_row(cards)


def _paired(cards: Sequence[Card], places: int) -> bool:
    """Whether these cards number that many and two of them share a rank."""
    return len(cards) == places and max(Counter(card.rank for card in cards).values()) >= PAIR_CARDS


def _pair_beside_a_suit(cards: Sequence[Card]) -> bool:
    """Whether five cards split into two of one rank beside three of one suit, each holding its own."""
    if len(cards) != PAIR_CARDS + SHORT_RUN:
        return False

    for places in combinations(range(len(cards)), PAIR_CARDS):
        pair = [cards[place] for place in places]
        rest = [card for place, card in enumerate(cards) if place not in places]
        if _alike(pair, PAIR_CARDS) and _suited(rest, SHORT_RUN):
            return True

    return False


@dataclass(frozen=True)
class RuleCase(Case):
    """One pattern beside a statement of the rule it carries, written from the definition of that rule.

    The statement is the reference the search is held against, so it says what a combination is and leaves
    how to look for one alone.
    """

    pattern: Pattern
    holds: Callable[[Sequence[Card]], bool]


RULES: Final[tuple[RuleCase, ...]] = (
    RuleCase(
        description="a pair is two cards of one rank",
        pattern=PAIR,
        holds=lambda cards: _alike(cards, PAIR_CARDS),
    ),
    RuleCase(
        description="a triplet is three cards of one rank",
        pattern=TRIPLET,
        holds=lambda cards: _alike(cards, TRIPLET_CARDS),
    ),
    RuleCase(
        description="a quadruplet is four cards of one rank",
        pattern=QUADRUPLET,
        holds=lambda cards: _alike(cards, SHORT_HAND),
    ),
    RuleCase(
        description="two pair are two ranks each held twice",
        pattern=TWO_PAIR,
        holds=lambda cards: _shared(cards, [PAIR_CARDS, PAIR_CARDS]),
    ),
    RuleCase(
        description="a full house is one rank held three times beside another held twice",
        pattern=FULL_HOUSE,
        holds=lambda cards: _shared(cards, [PAIR_CARDS, TRIPLET_CARDS]),
    ),
    RuleCase(
        description="three of a suit are three cards of one suit",
        pattern=SameSuit(places=SHORT_RUN),
        holds=lambda cards: _suited(cards, SHORT_RUN),
    ),
    RuleCase(
        description="a run of three is three cards in a row",
        pattern=Run(places=SHORT_RUN),
        holds=lambda cards: _run(cards, SHORT_RUN),
    ),
    RuleCase(
        description="a suited run of three is three cards of one suit in a row",
        pattern=Together(parts=(Run(places=SHORT_RUN), SameSuit(places=SHORT_RUN))),
        holds=lambda cards: _run(cards, SHORT_RUN) and _suited(cards, SHORT_RUN),
    ),
    RuleCase(
        description="a straight is five cards in a row",
        pattern=STRAIGHT,
        holds=lambda cards: _run(cards, POKER_HAND),
    ),
    RuleCase(
        description="five of a rank is five cards of one rank, which two decks reach",
        pattern=SameRank(places=POKER_HAND),
        holds=lambda cards: _alike(cards, POKER_HAND),
    ),
    RuleCase(
        description="a pair beside loose places is five cards, two of them sharing a rank",
        pattern=Beside(parts=(PAIR, AnyCards(places=SHORT_RUN))),
        holds=lambda cards: _paired(cards, POKER_HAND),
    ),
    RuleCase(
        description="a pair beside three of a suit holds both out of cards of their own",
        pattern=Beside(parts=(PAIR, SameSuit(places=SHORT_RUN))),
        holds=_pair_beside_a_suit,
    ),
)
SHORT_RULES: Final[tuple[RuleCase, ...]] = tuple(rule for rule in RULES if rule.pattern.size <= SHORT_HAND)


@st.composite
def _hands(draw: st.DrawFn, cards: int, wilds: int) -> tuple[CardOrJoker, ...]:
    naturals = draw(st.lists(st.sampled_from(SMALL_DECK), max_size=cards))
    jokers = draw(st.lists(st.sampled_from(JOKERS), max_size=min(wilds, cards - len(naturals))))
    return (*naturals, *jokers)


def _readings(cards: Sequence[CardOrJoker]) -> Iterator[tuple[Card, ...]]:
    """Every way of reading the jokers among these cards as cards of the whole deck."""
    places = tuple(place for place, card in enumerate(cards) if isinstance(card, Joker))
    if not places:
        yield tuple(card for card in cards if isinstance(card, Card))
        return

    for substitution in product(STANDARD_CARDS, repeat=len(places)):
        reading = list(cards)
        for place, card in zip(places, substitution, strict=True):
            reading[place] = card

        yield tuple(card for card in reading if isinstance(card, Card))


def _held(cards: Sequence[CardOrJoker], rule: RuleCase) -> bool:
    """Whether any selection of that many cards, read every way its jokers allow, answers the rule."""
    return any(
        rule.holds(reading) for selection in combinations(cards, rule.pattern.size) for reading in _readings(selection)
    )


@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(hand=_hands(cards=6, wilds=1), rule=st.sampled_from(RULES))
def test_the_search_finds_what_trying_every_selection_finds(hand: tuple[CardOrJoker, ...], rule: RuleCase) -> None:
    assert contains(hand, rule.pattern, REGULAR_EVALUATION) is _held(hand, rule)


@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(hand=_hands(cards=6, wilds=1), rule=st.sampled_from(RULES))
def test_a_whole_hand_answers_a_rule_only_where_a_reading_of_it_does(
    hand: tuple[CardOrJoker, ...], rule: RuleCase
) -> None:
    read_as_it_stands = any(rule.holds(reading) for reading in _readings(hand))

    assert matches(hand, rule.pattern, REGULAR_EVALUATION) is read_as_it_stands


@settings(deadline=None, max_examples=25, suppress_health_check=[HealthCheck.too_slow])
@given(hand=_hands(cards=SHORT_HAND, wilds=2), rule=st.sampled_from(SHORT_RULES))
def test_two_jokers_reach_exactly_as_far_as_trying_every_reading(hand: tuple[CardOrJoker, ...], rule: RuleCase) -> None:
    assert contains(hand, rule.pattern, REGULAR_EVALUATION) is _held(hand, rule)
