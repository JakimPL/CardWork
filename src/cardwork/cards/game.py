from __future__ import annotations

from typing import cast

from cardwork.cards.card import Card
from cardwork.cards.joker import Joker
from cardwork.models.base import BaseFrozen

CardOrJoker = Card | Joker

type CardsOrJokers = tuple[CardOrJoker, ...]


class GameCard(BaseFrozen):
    card: CardOrJoker
    face_down: bool = False

    @property
    def is_joker(self) -> bool:
        return isinstance(self.card, Joker)

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
        return game_card.is_joker

    return isinstance(game_card, Joker)


def suited(card: CardOrJoker) -> Card:
    """The card read as a suited one, which every card of the deck this game is played with is.

    Raises:
        ValueError: when the card is a joker, which the one standard deck of this game holds none of.
    """
    if is_joker(card):
        raise ValueError(f"This game is played with suited cards alone, and read {card}")

    return cast(Card, card)
