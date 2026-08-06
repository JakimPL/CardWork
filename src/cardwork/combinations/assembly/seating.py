from collections.abc import Sequence
from dataclasses import dataclass
from typing import Self

from cardwork.cards.card import Card, Cards
from cardwork.combinations.assembly.gates import Gates
from cardwork.combinations.matching import Seat
from cardwork.combinations.shape import Shape
from cardwork.combinations.spread import Spread


@dataclass(frozen=True)
class Seating:
    """The seats a run of cards answers in one shape, beside how many gates those seats pass through.

    A card answers a place where the demand standing there admits it, and it reaches that place through a gate.
    A place reading apart in a spread is reached through the gate that spread keeps for the facing the card
    shows, so two cards facing alike reach one place of that spread between them and holding places apart falls
    to the matching. A place reading apart in no spread is reached through a gate of its own, which leaves the
    place the whole of what it asks.
    """

    seats: tuple[tuple[Seat, ...], ...]
    gates: int

    @classmethod
    def of(
        cls,
        cards: Cards,
        shape: Shape,
        spreading: Sequence[Spread | None],
    ) -> Self:
        """The seats these cards answer, each card's own in the order it stands in."""
        gates = Gates(shape.size)
        seats = tuple(cls._answered(card, shape, spreading, gates) for card in cards)

        return cls(seats=seats, gates=len(gates))

    @staticmethod
    def _answered(
        card: Card,
        shape: Shape,
        spreading: Sequence[Spread | None],
        gates: Gates,
    ) -> tuple[Seat, ...]:
        """The seats this card answers: each place whose demand admits it, beside the gate it reaches through."""
        return tuple(
            (place, gates.of(place, spreading[place], card))
            for place, demand in enumerate(shape.demands)
            if demand.admits(card)
        )
