from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.order import ByRank, BySuit
from cardwork.cards.rank import Rank, Ranks
from cardwork.cards.suit import Suit, Suits
from cardwork.ordering.composite import Composite
from cardwork.ordering.preorder import Preorder

RANK_SEQUENCE: Final[Ranks] = tuple(Rank)
ACE_LOW_RANKS: Final[Ranks] = (Rank.ACE, *RANK_SEQUENCE[:-1])
SUIT_SEQUENCE: Final[Suits] = (Suit.CLUB, Suit.DIAMOND, Suit.HEART, Suit.SPADE)

BY_RANK: Final[Preorder[Card]] = ByRank(RANK_SEQUENCE)
BY_RANK_ACE_LOW: Final[Preorder[Card]] = ByRank(ACE_LOW_RANKS)
BY_SUIT: Final[Preorder[Card]] = BySuit(SUIT_SEQUENCE)
REGULAR_ORDER: Final[Preorder[Card]] = Composite(BY_RANK, BY_SUIT)
