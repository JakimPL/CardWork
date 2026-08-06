from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.cards.cards import ACE_OF_SPADES, BLACK_JOKER, KING_OF_HEARTS, QUEEN_OF_CLUBS, RED_JOKER
from cardwork.cards.game import CardsOrJokers, GameCard
from cardwork.decks.deck import Indices
from cardwork.decks.decks import (
    compare_decks,
    count_cards,
    does_contain_jokers,
    jokers,
    named,
    normalize_deck,
    to_game_cards,
)
from tests.cases import Case, descriptions

RUN: Final[CardsOrJokers] = (ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS)
PAST_THE_RUN: Final[int] = len(RUN)


@dataclass(frozen=True)
class NamingCase(Case):
    """One run of places and the cards of a three-card run they name."""

    indices: Indices
    read: CardsOrJokers


NAMINGS: Final[tuple[NamingCase, ...]] = (
    NamingCase(description="no place at all", indices=frozenset(), read=()),
    NamingCase(description="one place of the run", indices=frozenset({1}), read=(KING_OF_HEARTS,)),
    NamingCase(
        description="places named in the run's own order",
        indices=frozenset({0, 1}),
        read=(ACE_OF_SPADES, KING_OF_HEARTS),
    ),
    NamingCase(
        description="places named the other way round",
        indices=frozenset({2, 0}),
        read=(ACE_OF_SPADES, QUEEN_OF_CLUBS),
    ),
    NamingCase(description="every place of the run", indices=frozenset({0, 1, 2}), read=RUN),
)


@pytest.mark.parametrize("case", NAMINGS, ids=descriptions(NAMINGS))
def test_named_reads_the_cards_standing_at_the_places_given(case: NamingCase) -> None:
    assert named(RUN, case.indices) == case.read


def test_named_refuses_a_place_lying_past_the_end_of_the_run() -> None:
    with pytest.raises(KeyError, match=f"Place {PAST_THE_RUN} lies past the {len(RUN)} cards"):
        named(RUN, frozenset({PAST_THE_RUN}))


def test_named_reads_no_place_of_a_run_holding_no_cards() -> None:
    assert named((), frozenset()) == ()


def test_normalize_deck_unwraps_game_cards() -> None:
    deck = (GameCard(card=ACE_OF_SPADES, face_down=True), KING_OF_HEARTS)

    assert normalize_deck(deck) == [ACE_OF_SPADES, KING_OF_HEARTS]


def test_count_cards_ignores_the_face() -> None:
    deck = (GameCard(card=ACE_OF_SPADES, face_down=True), GameCard(card=ACE_OF_SPADES, face_down=False))

    assert count_cards(deck) == {ACE_OF_SPADES: 2}


def test_compare_decks_ignores_order_and_wrapping() -> None:
    assert compare_decks((ACE_OF_SPADES, KING_OF_HEARTS), (KING_OF_HEARTS, GameCard(card=ACE_OF_SPADES)))


def test_compare_decks_detects_a_missing_card() -> None:
    assert not compare_decks((ACE_OF_SPADES, KING_OF_HEARTS), (ACE_OF_SPADES,))


def test_jokers_builds_the_requested_colours() -> None:
    assert jokers(black=2, red=1) == (BLACK_JOKER, BLACK_JOKER, RED_JOKER)


def test_does_contain_jokers_detects_a_single_joker() -> None:
    assert does_contain_jokers((ACE_OF_SPADES, RED_JOKER))
    assert not does_contain_jokers((ACE_OF_SPADES, KING_OF_HEARTS))


def test_to_game_cards_gives_every_card_the_requested_face() -> None:
    wrapped = to_game_cards((ACE_OF_SPADES, KING_OF_HEARTS), face_down=True)

    assert wrapped == (GameCard(card=ACE_OF_SPADES, face_down=True), GameCard(card=KING_OF_HEARTS, face_down=True))


def test_to_game_cards_restates_the_face_of_already_wrapped_cards() -> None:
    wrapped = to_game_cards((GameCard(card=ACE_OF_SPADES, face_down=True),), face_down=False)

    assert wrapped == (GameCard(card=ACE_OF_SPADES, face_down=False),)
