from collections.abc import Iterable

from cardwork.cards.game import CardOrJoker, GameCard

Deck = tuple[CardOrJoker, ...]
GameDeck = Iterable[CardOrJoker] | Iterable[GameCard]

Indices = frozenset[int]
GameCards = tuple[GameCard, ...]
