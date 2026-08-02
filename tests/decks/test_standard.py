from typing import Final

from cardwork.decks.standard import is_standard_deck, standard_deck

FULL_DECK_SIZE: Final[int] = 52


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
