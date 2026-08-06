from collections.abc import Sequence
from typing import Self

from cardwork.cards.card import Card, Facing
from cardwork.combinations.spread import Spread


class Naming:
    """What a reading names as it fills in, which is what a joker standing at an open place reads apart from.

    A joker reads as a card the reading leaves free: one it does not name already, and at a place reading apart,
    one showing a facing the spread of that place leaves free as well. Both grow as each joker is read, so the
    jokers of a reading stand apart from one another as they do from the cards held.
    """

    def __init__(self, spreading: Sequence[Spread | None]) -> None:
        self._spreading = spreading
        self._named: set[Card] = set()
        self._facings: dict[Spread, set[Facing]] = {spread: set() for spread in set(spreading) if spread is not None}

    @classmethod
    def of(cls, standing: Sequence[Card | None], spreading: Sequence[Spread | None]) -> Self:
        """What the cards holding these places name, which leaves the open places to the jokers."""
        naming = cls(spreading)
        for place, card in enumerate(standing):
            if card is not None:
                naming.take(place, card)

        return naming

    def take(self, place: int, card: Card) -> None:
        """Name that card at that place, so whatever stands after it reads apart from it."""
        self._named.add(card)
        spread = self._spreading[place]
        if spread is not None:
            self._facings[spread].add(spread.read(card))

    def leaves(self, place: int, card: Card) -> bool:
        """Whether this reading leaves the card free at that place, naming neither it nor its facing there."""
        if card in self._named:
            return False

        spread = self._spreading[place]
        return spread is None or spread.read(card) not in self._facings[spread]
