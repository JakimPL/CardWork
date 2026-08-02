from cardwork.cards.card import Card
from cardwork.cards.joker import Joker
from cardwork.models.base import BaseFrozen

CardOrJoker = Card | Joker


class GameCard(BaseFrozen):
    card: CardOrJoker
    face_down: bool = False

    def __str__(self) -> str:
        hidden = "?" if self.face_down else ""
        return f"{self.card!s}{hidden}"

    def __repr__(self) -> str:
        return str(self)


def is_joker(game_card: CardOrJoker | GameCard) -> bool:
    if isinstance(game_card, GameCard):
        return isinstance(game_card.card, Joker)

    return isinstance(game_card, Joker)
