from pydantic import Field

from cardwork.cards.card import Card
from cardwork.cards.joker import Joker
from cardwork.models.base import Base

CardOrJoker = Card | Joker


class GameCard(Base):
    card: CardOrJoker = Field(frozen=True)
    hidden: bool = False

    def __str__(self) -> str:
        hidden = "?" if self.hidden else ""
        return f"{str(self.card)}{hidden}"

    def __repr__(self) -> str:
        return str(self)


def is_joker(game_card: CardOrJoker | GameCard) -> bool:
    if isinstance(game_card, GameCard):
        return isinstance(game_card.card, Joker)

    return isinstance(game_card, Joker)
