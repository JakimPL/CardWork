from pydantic import BaseModel

from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit


class Card(BaseModel, extra="forbid", frozen=True):
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"

    def __repr__(self) -> str:
        return str(self)
