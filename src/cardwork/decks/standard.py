from cardwork.cards.cards import STANDARD_CARDS
from cardwork.decks.deck import Deck, GameDeck
from cardwork.decks.decks import compare_decks, jokers


def standard_deck(
    *,
    black_jokers: int = 0,
    red_jokers: int = 0,
) -> Deck:
    return (
        *STANDARD_CARDS,
        *jokers(
            black=black_jokers,
            red=red_jokers,
        ),
    )


def is_standard_deck(
    deck: GameDeck,
    *,
    black_jokers: int = 0,
    red_jokers: int = 0,
) -> bool:
    return compare_decks(
        deck,
        standard_deck(
            black_jokers=black_jokers,
            red_jokers=red_jokers,
        ),
    )
