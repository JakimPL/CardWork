from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.decks.deck import Deck, GameDeck
from cardwork.decks.decks import compare_decks, jokers

STANDARD_DECK: Final[Deck] = tuple(
    Card(
        rank=rank,
        suit=suit,
    )
    for rank in Rank
    for suit in Suit
)


def standard_deck(
    *,
    black_jokers: int = 0,
    red_jokers: int = 0,
) -> Deck:
    return (
        *STANDARD_DECK,
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
