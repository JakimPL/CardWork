from cardwork.cards.suit import Suit
from cardwork.models.base import BaseFrozen


class Joker(BaseFrozen):
    red: bool

    def __str__(self) -> str:
        color = Suit.HEART.value if self.red else Suit.SPADE.value
        return f"*{color}"

    def __repr__(self) -> str:
        return str(self)
