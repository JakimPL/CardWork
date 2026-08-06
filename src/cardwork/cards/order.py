from collections.abc import Sequence

from cardwork.cards.card import Card
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.ordering.preorder import Key, Preorder
from cardwork.ordering.tiers import Tiers


class ByRank(Preorder[Card]):
    """Cards placed by rank alone, which holds every card of one rank alongside the others.

    This is the preorder proper, and the one a game compares under when it wants the tie itself. A game
    that wants a single winner out of any pair refines it with a suit order.
    """

    def __init__(self, ranks: Sequence[Rank]) -> None:
        self._ranks = Tiers(ranks)

    def key(self, value: Card) -> Key:
        return self._ranks.key(value.rank)


class BySuit(Preorder[Card]):
    """Cards placed by suit alone, which is what settles a tie of rank."""

    def __init__(self, suits: Sequence[Suit]) -> None:
        self._suits = Tiers(suits)

    def key(self, value: Card) -> Key:
        return self._suits.key(value.suit)
