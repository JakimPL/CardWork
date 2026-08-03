from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.cards.cards import TWO_OF_SPADES
from cardwork.decks.deck import Deck
from cardwork.decks.decks import compare_decks, jokers
from cardwork.decks.standard import (
    NO_WHOLE_DECKS,
    ONE_DECK,
    is_standard_deck,
    standard_deck,
    standard_decks,
    standard_multiplicity,
)

from ..cases import Case, descriptions

FULL_DECK_SIZE: Final[int] = 52
TWO_DECKS: Final[int] = 2
NO_DECKS: Final[int] = 0


def test_standard_deck_holds_every_rank_and_suit_once() -> None:
    deck = standard_deck()

    assert len(deck) == FULL_DECK_SIZE
    assert len(set(deck)) == FULL_DECK_SIZE


def test_standard_deck_appends_the_requested_jokers() -> None:
    deck = standard_deck(black_jokers=1, red_jokers=2)

    assert len(deck) == FULL_DECK_SIZE + 3


def test_is_standard_deck_requires_a_matching_joker_count() -> None:
    deck = standard_deck(red_jokers=1)

    assert is_standard_deck(deck, red_jokers=1)
    assert not is_standard_deck(deck)


def test_several_standard_decks_hold_every_card_that_many_times() -> None:
    deck = standard_decks(TWO_DECKS, black_jokers=1, red_jokers=1)

    assert len(deck) == TWO_DECKS * FULL_DECK_SIZE + TWO_DECKS
    assert deck.count(TWO_OF_SPADES) == TWO_DECKS
    assert compare_decks(deck, standard_deck() + standard_deck() + jokers(black=1, red=1))


def test_one_standard_deck_is_the_deck_a_single_count_asks_for() -> None:
    assert compare_decks(
        standard_decks(ONE_DECK, black_jokers=1, red_jokers=0),
        standard_deck(black_jokers=1),
    )


def test_a_deck_is_made_of_at_least_one_standard_deck() -> None:
    with pytest.raises(ValueError, match="at least 1 standard deck"):
        standard_decks(NO_DECKS, black_jokers=0, red_jokers=0)


@dataclass(frozen=True)
class MultiplicityCase(Case):
    deck: Deck
    decks: int


MULTIPLICITIES: Final[tuple[MultiplicityCase, ...]] = (
    MultiplicityCase(
        description="one standard deck makes one",
        deck=standard_deck(),
        decks=ONE_DECK,
    ),
    MultiplicityCase(
        description="jokers stand outside the count",
        deck=standard_deck(black_jokers=1, red_jokers=2),
        decks=ONE_DECK,
    ),
    MultiplicityCase(
        description="two standard decks make two",
        deck=standard_decks(TWO_DECKS, black_jokers=0, red_jokers=0),
        decks=TWO_DECKS,
    ),
    MultiplicityCase(
        description="two standard decks make two beside their jokers",
        deck=standard_decks(TWO_DECKS, black_jokers=2, red_jokers=2),
        decks=TWO_DECKS,
    ),
    MultiplicityCase(
        description="a deck one card short makes none",
        deck=standard_deck()[:-1],
        decks=NO_WHOLE_DECKS,
    ),
    MultiplicityCase(
        description="a deck holding one card twice makes none",
        deck=standard_deck() + (TWO_OF_SPADES,),
        decks=NO_WHOLE_DECKS,
    ),
    MultiplicityCase(
        description="jokers alone make none",
        deck=jokers(black=1, red=1),
        decks=NO_WHOLE_DECKS,
    ),
    MultiplicityCase(
        description="no cards make none",
        deck=(),
        decks=NO_WHOLE_DECKS,
    ),
)


@pytest.mark.parametrize("case", MULTIPLICITIES, ids=descriptions(MULTIPLICITIES))
def test_the_multiplicity_counts_the_whole_standard_decks_the_suited_cards_make(case: MultiplicityCase) -> None:
    assert standard_multiplicity(case.deck) == case.decks
