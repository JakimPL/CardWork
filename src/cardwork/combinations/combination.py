from typing import Final, Self

from pydantic import model_validator

from cardwork.cards.game import CardsOrJokers
from cardwork.combinations.pattern import AnyPattern, Reading
from cardwork.combinations.policy import Evaluation
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

    pattern: AnyPattern
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


class ByReading(Preorder[Combination]):
    """Combinations by the cards they read as, the strongest card first, under one reading of the deck.

    A pattern states its strength in ranks, so a pair of kings shares a place with every other pair of kings.
    This order reads the cards themselves — each by rank and then by suit, as the evaluation places them — and
    so gives two combinations one place exactly where they read as the same cards. Refining a strength order
    with it is how a game that needs one winner out of every contest states that rule.

    A joker reads as the card it stands in for, so it takes the place that card takes.
    """

    def __init__(self, evaluation: Evaluation) -> None:
        self._cards = evaluation.card_order()

    def key(self, value: Combination) -> Key:
        return tuple(place for card in self._cards.descending(value.reading) for place in self._cards.key(card))


BY_STRENGTH: Final[Preorder[Combination]] = ByStrength()
