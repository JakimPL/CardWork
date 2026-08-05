from __future__ import annotations

from collections.abc import Iterable
from typing import overload

from cardwork.cards.card import Card, Cards
from cardwork.cards.joker import Joker
from cardwork.exceptions import LogicError
from cardwork.models.base import BaseFrozen

type CardOrJoker = Card | Joker
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


@overload
def suited(game_cards: Iterable[CardOrJoker] | Iterable[GameCard]) -> Cards: ...


@overload
def suited(game_cards: CardOrJoker | GameCard) -> Card: ...


def suited(
    game_cards: CardOrJoker | GameCard | Iterable[CardOrJoker] | Iterable[GameCard],
) -> Card | Cards:
    """The card read as a suited one, which every card of the deck this game is played with is.

    Raises:
        LogicError: when the card is a joker, which the one standard deck of this game holds none of.
    """
    single = isinstance(game_cards, (Card, Joker, GameCard))
    iterable = (game_cards,) if single else game_cards

    result: list[Card] = []

    for obj in iterable:
        card = obj.card if isinstance(obj, GameCard) else obj
        if not isinstance(card, Card):
            raise LogicError(f"This game is played with suited cards alone, and read {card}")

        result.append(card)

    return result[0] if single else tuple(result)
