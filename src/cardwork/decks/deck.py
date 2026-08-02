from collections.abc import Iterable
from typing import Annotated

from pydantic import Field

from cardwork.cards.game import CardOrJoker, GameCard

Deck = tuple[CardOrJoker, ...]
GameDeck = Iterable[CardOrJoker] | Iterable[GameCard]

Indices = frozenset[int]
NonEmptyIndices = Annotated[Indices, Field(min_length=1)]
GameCards = tuple[GameCard, ...]
