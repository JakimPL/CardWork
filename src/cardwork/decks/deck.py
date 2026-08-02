from collections import deque
from collections.abc import Iterable

from cardwork.cards.game import CardOrJoker, GameCard

Deck = tuple[CardOrJoker, ...]
GameDeck = Iterable[CardOrJoker] | Iterable[GameCard]

Indices = set[int]
Group = list[GameCard]
Stack = deque[GameCard]
Variant = Group | Stack
