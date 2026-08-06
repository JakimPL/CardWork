from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cardwork.cards.card import Card, Facing


class Facet(StrEnum):
    """What a spread reads of the card standing at a place, which the places of one spread each read its own of.

    `CARD` reads the card itself, so a place takes a card the other places of the spread left; `RANK` and
    `SUIT` read one side of it. Over one rank a card of one's own and a suit of one's own say the same thing,
    and over one suit a card of one's own and a rank of one's own do. They part where a spread reaches over
    several ranks and several suits at once, which is what tells a pair holding two suits from two pairs
    holding four.
    """

    CARD = "card"
    RANK = "rank"
    SUIT = "suit"


@dataclass(frozen=True)
class Spread:
    """Places that read apart, each of them taking a facet of its own.

    Several decks in play let one card answer two places asking alike, so a shape states a spread for the
    places a rule holds apart and the fill honours it: two copies of the king of spades answer one place of a
    spread between them. `Apart` is the pattern that states a spread, and `Shape.beside` and `Shape.together`
    carry the spreads of the readings they build from.
    """

    facet: Facet
    places: frozenset[int]

    def read(self, card: Card) -> Facing:
        """The facet of the card that this spread holds its places to."""
        match self.facet:
            case Facet.CARD:
                return card
            case Facet.RANK:
                return card.rank
            case Facet.SUIT:
                return card.suit

    def holds(self, place: int) -> bool:
        """Whether that place reads apart from the others this spread names."""
        return place in self.places

    def shifted(self, by: int) -> Spread:
        """The same spread over places counted from there, which standing beside other places asks for."""
        return Spread(facet=self.facet, places=frozenset(place + by for place in self.places))
