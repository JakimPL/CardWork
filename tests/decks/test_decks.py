from cardwork.cards.cards import ACE_OF_SPADES, BLACK_JOKER, KING_OF_HEARTS, RED_JOKER
from cardwork.cards.game import GameCard
from cardwork.decks.decks import compare_decks, count_cards, does_contain_jokers, jokers, normalize_deck


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
