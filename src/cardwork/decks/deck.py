from collections.abc import Iterable
from typing import Annotated

from pydantic import Field

from cardwork.cards.game import CardOrJoker, CardsOrJokers, GameCard

type Deck = CardsOrJokers
type GameDeck = Iterable[CardOrJoker] | Iterable[GameCard]

type CardIndex = Annotated[int, Field(ge=0)]
type Indices = frozenset[CardIndex]
type NonEmptyIndices = Annotated[Indices, Field(min_length=1)]
type GameCards = tuple[GameCard, ...]
