from pydantic import BaseModel

from cardwork.cards.suit import Suit


class Joker(BaseModel, extra="forbid", frozen=True):
    red: bool

    def __str__(self) -> str:
        color = Suit.HEART.value if self.red else Suit.SPADE.value
        return f"*{color}"

    def __repr__(self) -> str:
        return str(self)
