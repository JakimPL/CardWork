from pydantic import BaseModel

from cardwork.cards.card import Card
from cardwork.cards.joker import Joker


class GameCard(BaseModel, extra="forbid", frozen=True):
    card: Card | Joker
    hidden: bool = False

    def __str__(self) -> str:
        hidden = "?" if self.hidden else ""
        return f"{str(self.card)}{hidden}"

    def __repr__(self) -> str:
        return str(self)
