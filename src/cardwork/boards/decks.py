from collections import Counter
from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.deck import Deck, GameDeck
from cardwork.cards.game import GameCard
from cardwork.cards.joker import Joker
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit

STANDARD_DECK: Final[Deck] = tuple(
    Card(
        rank=rank,
        suit=suit,
    )
    for rank in Rank
    for suit in Suit
)


def normalize_deck(deck: GameDeck) -> list[Card | Joker]:
    return [game_card.card if isinstance(game_card, GameCard) else game_card for game_card in deck]


def compare_decks(deck1: GameDeck, deck2: GameDeck) -> bool:
    normalized_deck1 = normalize_deck(deck1)
    normalized_deck2 = normalize_deck(deck2)
    return Counter(normalized_deck1) == Counter(normalized_deck2)


def is_standard_deck(
    deck: GameDeck,
    *,
    black_jockers: int = 0,
    red_jokers: int = 0,
) -> bool:
    normalized_deck = normalize_deck(deck)
    jockers_count = black_jockers + red_jokers
    jokers = [Joker(red=index >= black_jockers) for index in range(jockers_count)]
    return compare_decks([*normalized_deck, *jokers], STANDARD_DECK)
