from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.models.base import BaseFrozen


class Card(BaseFrozen):
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"

    def __repr__(self) -> str:
        return str(self)


type Cards = tuple[Card, ...]
