from collections import deque
from collections.abc import Iterable

from cardwork.cards.card import Card
from cardwork.cards.game import GameCard
from cardwork.cards.joker import Joker

Deck = tuple[Card | Joker, ...]
GameDeck = Iterable[Card | Joker] | Iterable[GameCard]

Group = list[GameCard]
Stack = deque[GameCard]
Variant = Group | Stack
