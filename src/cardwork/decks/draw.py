import random

from cardwork.decks.deck import Deck


def shuffle_deck(deck: Deck, rng: random.Random | None = None) -> Deck:
    generator = rng or random
    shuffled = list(deck)
    generator.shuffle(shuffled)
    return tuple(shuffled)
