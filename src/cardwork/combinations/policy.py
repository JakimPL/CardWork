from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Final, Self

from pydantic import model_validator

from cardwork.cards.card import Card
from cardwork.cards.order import RANK_SEQUENCE, SUIT_SEQUENCE, ByRank, BySuit
from cardwork.cards.rank import Rank, Ranks
from cardwork.cards.suit import Suit, Suits
from cardwork.models.base import BaseFrozen
from cardwork.ordering.preorder import Composite, Preorder


class Duplicates(StrEnum):
    """How a game reads one card held twice, which several standard decks in play make possible.

    Under `COUNT` each copy answers for itself, so two two of diamonds and one three of diamonds are three
    diamonds. Under `COLLAPSE` a repeated card is read once, so the same three cards are two diamonds.
    """

    COUNT = "count"
    COLLAPSE = "collapse"


class Evaluation(BaseFrozen):
    """How a game reads its cards when it looks for combinations.

    `ranks` is the sequence a run follows and the strength a rank carries, lowest first; `suits` does the
    same for suits. Both list the whole deck, so every card takes a place. `wheel` admits the run that
    begins on the highest rank and continues from the lowest — A 2 3 4 5, where the ace acts as one.
    `wild_jokers` lets a joker stand in for whatever a combination asks of it, and `duplicates` states how
    a repeated card counts.
    """

    ranks: Ranks
    suits: Suits
    wheel: bool
    wild_jokers: bool
    duplicates: Duplicates

    @model_validator(mode="after")
    def _every_card_takes_a_place(self) -> Self:
        self._placed(self.ranks, tuple(Rank), "rank")
        self._placed(self.suits, tuple(Suit), "suit")
        return self

    def rank_places(self) -> Mapping[Rank, int]:
        """Where each rank stands in the sequence, counting from the lowest."""
        return {rank: place for place, rank in enumerate(self.ranks)}

    def card_order(self) -> Preorder[Card]:
        """Cards by rank and then by suit, which is the strength this reading gives a single card."""
        return Composite(ByRank(self.ranks), BySuit(self.suits))

    @staticmethod
    def _placed[ValueT](
        listed: Sequence[ValueT],
        deck: Sequence[ValueT],
        subject: str,
    ) -> None:
        """Confirm the sequence gives each of the deck's values one place of its own.

        Raises:
            ValueError: when a value of the deck is left out, or when one of them is listed twice.
        """
        left_out = tuple(value for value in deck if value not in listed)
        if left_out:
            raise ValueError(f"A reading places every {subject} of the deck, and these are left out: {left_out}")

        places = len(set(listed))
        if places != len(listed):
            raise ValueError(f"Every {subject} takes one place, and {len(listed)} of them fill {places}")


REGULAR_EVALUATION: Final[Evaluation] = Evaluation(
    ranks=RANK_SEQUENCE,
    suits=SUIT_SEQUENCE,
    wheel=True,
    wild_jokers=True,
    duplicates=Duplicates.COUNT,
)
