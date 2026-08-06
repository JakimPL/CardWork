from typing import Final

from cardwork.cards.orders import ACE_LOW_RANKS
from cardwork.cards.rank import Ranks
from cardwork.combinations.combination import Combination
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.patterns.any_cards import AnyCards
from cardwork.combinations.patterns.beside import Beside
from cardwork.combinations.patterns.run import Run
from cardwork.combinations.patterns.same_rank import SameRank
from cardwork.combinations.patterns.same_suit import SameSuit
from cardwork.combinations.patterns.together import Together
from cardwork.combinations.policy import REGULAR_EVALUATION
from cardwork.combinations.ranking import Ranking
from cardwork.ordering.preorder import Preorder

POKER_HAND: Final[int] = 5
WHEEL: Final[Ranks] = ACE_LOW_RANKS[:POKER_HAND]

HIGH_CARD: Final[Pattern] = AnyCards(places=1)
PAIR: Final[Pattern] = SameRank(places=2)
TRIPLET: Final[Pattern] = SameRank(places=3)
QUADRUPLET: Final[Pattern] = SameRank(places=4)
TWO_PAIR: Final[Pattern] = Beside(parts=(PAIR, PAIR))
FULL_HOUSE: Final[Pattern] = Beside(parts=(TRIPLET, PAIR))
QUADRUPLET_WITH_ONE: Final[Pattern] = Beside(parts=(QUADRUPLET, HIGH_CARD))
STRAIGHT: Final[Pattern] = Run(places=POKER_HAND)
FLUSH: Final[Pattern] = SameSuit(places=POKER_HAND)
STRAIGHT_FLUSH: Final[Pattern] = Together(parts=(STRAIGHT, FLUSH))

POKER: Final[Ranking] = Ranking(
    patterns=(
        HIGH_CARD,
        PAIR,
        TWO_PAIR,
        TRIPLET,
        STRAIGHT,
        FLUSH,
        FULL_HOUSE,
        QUADRUPLET,
        STRAIGHT_FLUSH,
    ),
    evaluation=REGULAR_EVALUATION,
)

POKER_ORDER: Final[Preorder[Combination]] = POKER.total_order
