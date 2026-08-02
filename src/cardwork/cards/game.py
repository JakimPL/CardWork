from __future__ import annotations

from cardwork.cards.card import Card
from cardwork.cards.joker import Joker
from cardwork.models.base import BaseFrozen

CardOrJoker = Card | Joker


class GameCard(BaseFrozen):
    card: CardOrJoker
    face_down: bool = False

    def with_face(self, face_down: bool) -> GameCard:
        """The same card lying the given way up."""
        return GameCard(card=self.card, face_down=face_down)

    def __str__(self) -> str:
        hidden = "?" if self.face_down else ""
        return f"{self.card!s}{hidden}"

    def __repr__(self) -> str:
        return str(self)


def is_joker(game_card: CardOrJoker | GameCard) -> bool:
    if isinstance(game_card, GameCard):
        return isinstance(game_card.card, Joker)

    return isinstance(game_card, Joker)
