from typing import Final, Self

from pydantic import SerializeAsAny, model_validator

from cardwork.cards.game import CardsOrJokers
from cardwork.combinations.pattern import Pattern, Reading
from cardwork.models.base import BaseFrozen
from cardwork.ordering.preorder import Key, Preorder


class Combination(BaseFrozen):
    """One instance of a pattern: the cards that make it, beside what each of them reads as.

    `cards` are the cards themselves, jokers included, in the order the pattern's places take them, and
    `reading` states what stands at each of those places, so `reading[place]` answers for `cards[place]`.
    A natural card reads as itself and a wild joker reads as the card it stands in for, which is what lets a
    game tell which card played which part and lets a scoring table count a joker for what it stood in for.

    `strength` places the instance among the others of its pattern, which the pattern itself states. Two
    instances reading one key stand alongside each other, so a game that settles such a tie by suit says so
    itself.

    `low_ace` holds where a run reads its highest rank as its lowest, which is the ace of A 2 3 4 5, and it
    is what a scoring table consults to count that ace as one.
    """

    pattern: SerializeAsAny[Pattern]
    cards: CardsOrJokers
    reading: Reading
    strength: Key
    low_ace: bool

    @model_validator(mode="after")
    def _every_place_holds_one_card_and_one_reading(self) -> Self:
        if len(self.cards) != len(self.reading):
            raise ValueError(f"Every card reads as one card, and {len(self.cards)} of them read as {len(self.reading)}")

        if len(self.cards) != self.pattern.size:
            raise ValueError(f"A {self.pattern} takes {self.pattern.size} cards, and this one holds {len(self.cards)}")

        return self

    def __str__(self) -> str:
        return f"{self.pattern}: {' '.join(str(card) for card in self.cards)}"

    def __repr__(self) -> str:
        return str(self)


class ByStrength(Preorder[Combination]):
    """Combinations of one pattern by the place the search read them into.

    Instances of different patterns compare here as well, and the comparison means little across patterns:
    a ranking states which pattern outranks which, and refines this order with it.
    """

    def key(self, value: Combination) -> Key:
        return value.strength


BY_STRENGTH: Final[Preorder[Combination]] = ByStrength()
