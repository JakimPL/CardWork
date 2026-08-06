from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from cardwork.cards.card import Card, Cards
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.combinations.policy import Evaluation


@dataclass(frozen=True)
class Demand:
    """What one place in a combination asks of the card that fills it.

    A rank alone asks for any card of that rank, as a triplet does; a suit alone asks for any card of that
    suit, as a flush does; both together ask for that one card, as a straight flush does; and neither asks
    for any card at all, as a loose place does. `of_rank` and `of_suit` name the two a pattern asks for most,
    and `ANY_CARD` is the loose place.
    """

    rank: Rank | None
    suit: Suit | None

    @classmethod
    def of_rank(cls, rank: Rank) -> Demand:
        """A place any card of that rank answers."""
        return cls(rank=rank, suit=None)

    @classmethod
    def of_suit(cls, suit: Suit) -> Demand:
        """A place any card of that suit answers."""
        return cls(rank=None, suit=suit)

    def admits(self, card: Card) -> bool:
        """Whether the card answers this place."""
        return (self.rank is None or card.rank == self.rank) and (self.suit is None or card.suit == self.suit)

    def meet(self, other: Demand) -> Demand | None:
        """What both demands ask of one place at once, and None where no card answers them both."""
        if self.rank is not None and other.rank is not None and self.rank != other.rank:
            return None

        if self.suit is not None and other.suit is not None and self.suit != other.suit:
            return None

        return Demand(
            rank=self.rank if self.rank is not None else other.rank,
            suit=self.suit if self.suit is not None else other.suit,
        )

    def candidates(self, evaluation: Evaluation) -> Cards:
        """Every card this place admits, the strongest first, whether a hand holds it or not."""
        ranks = (self.rank,) if self.rank is not None else tuple(reversed(evaluation.ranks))
        suits = (self.suit,) if self.suit is not None else tuple(reversed(evaluation.suits))
        return tuple(Card(rank=rank, suit=suit) for rank in ranks for suit in suits)


ANY_CARD: Final[Demand] = Demand(rank=None, suit=None)
