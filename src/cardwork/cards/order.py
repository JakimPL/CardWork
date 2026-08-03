from collections.abc import Sequence
from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.ordering.preorder import Composite, Key, Preorder, Tiers

RANK_SEQUENCE: Final[tuple[Rank, ...]] = tuple(Rank)
ACE_LOW_RANKS: Final[tuple[Rank, ...]] = (Rank.ACE, *RANK_SEQUENCE[:-1])
SUIT_SEQUENCE: Final[tuple[Suit, ...]] = (Suit.CLUB, Suit.DIAMOND, Suit.HEART, Suit.SPADE)


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


BY_RANK: Final[Preorder[Card]] = ByRank(RANK_SEQUENCE)
BY_RANK_ACE_LOW: Final[Preorder[Card]] = ByRank(ACE_LOW_RANKS)
BY_SUIT: Final[Preorder[Card]] = BySuit(SUIT_SEQUENCE)
REGULAR_ORDER: Final[Preorder[Card]] = Composite(BY_RANK, BY_SUIT)
