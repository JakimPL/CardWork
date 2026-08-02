import random

from cardwork.decks.deck import Deck


def shuffle_deck(deck: Deck) -> Deck:
    shuffled = list(deck)
    random.shuffle(shuffled)
    return tuple(shuffled)
