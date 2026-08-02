from collections.abc import Iterable
from typing import Annotated

from pydantic import Field

from cardwork.cards.game import CardOrJoker, GameCard

Deck = tuple[CardOrJoker, ...]
GameDeck = Iterable[CardOrJoker] | Iterable[GameCard]

CardIndex = Annotated[int, Field(ge=0)]
Indices = frozenset[CardIndex]
NonEmptyIndices = Annotated[Indices, Field(min_length=1)]
GameCards = tuple[GameCard, ...]
