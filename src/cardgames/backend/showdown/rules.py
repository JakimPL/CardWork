from collections.abc import Sequence
from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.game import CardOrJoker
from cardwork.cards.order import REGULAR_ORDER
from cardwork.cards.points import REGULAR_POINTS, PointTable
from cardwork.ordering.preorder import Preorder
from cardwork.states.state import Points

HAND_SIZE: Final[int] = 5
BLIND_SIZE: Final[int] = 5
TURNS: Final[int] = HAND_SIZE + BLIND_SIZE
FIRST_TURN: Final[int] = 1
ONE_TURN: Final[int] = 1
ONE_CARD: Final[int] = 1
NOTHING: Final[int] = 0
STRONGEST: Final[int] = 0

STRENGTH: Final[Preorder[Card]] = REGULAR_ORDER
POINTS: Final[PointTable] = REGULAR_POINTS


def suited(card: CardOrJoker) -> Card:
    """The card read as a suited one, which every card of the deck this game is played with is.

    Raises:
        ValueError: when the card is a joker, which the one standard deck of this game holds none of.
    """
    if isinstance(card, Card):
        return card

    raise ValueError(f"This game is played with suited cards alone, and read {card}")


def taken_by(revealed: Sequence[CardOrJoker]) -> int:
    """The place of the card taking the turn: the strongest by rank, a tie of rank settled by suit.

    `STRENGTH` is a total order, so one card of any run stands above the rest and a turn has exactly one winner.

    Raises:
        ValueError: when nothing was revealed, which a turn every seat commits to always leaves something in.
    """
    if not revealed:
        raise ValueError("A turn goes to the strongest of the cards revealed, and none were")

    return STRENGTH.argmaxima(tuple(suited(card) for card in revealed))[STRONGEST]


def turn_points(revealed: Sequence[CardOrJoker], winner: int) -> int:
    """What the turn is worth to the seat taking it, which is every other card revealed at its own worth."""
    return POINTS.total(card for place, card in enumerate(revealed) if place != winner)


def awarded(tally: Points, winner: int, taken: int) -> Points:
    """The round's tally with what a turn was worth added to the seat that took it."""
    return tuple(scored + (taken if seat == winner else NOTHING) for seat, scored in enumerate(tally))
