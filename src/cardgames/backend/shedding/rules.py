from collections.abc import Sequence
from typing import Final

from cardwork.cards.game import CardOrJoker
from cardwork.cards.orders import RANK_SEQUENCE, SUIT_SEQUENCE
from cardwork.combinations.patterns.same_rank import SameRank
from cardwork.combinations.policy import Duplicates, Evaluation
from cardwork.combinations.ranking import Ranking
from cardwork.decks.deck import Indices
from cardwork.exceptions import LogicError
from cardwork.states.award import Award

AWARD: Final[Award] = Award.HIGHEST
HAND_SIZE: Final[int] = 4
SHED_LEAST: Final[int] = 2
ALIKE_MOST: Final[int] = len(SUIT_SEQUENCE)
ONE_CARD: Final[int] = 1
ROUND_POINT: Final[int] = 1
NO_CARDS: Final[int] = 0

SEATS_LEAST: Final[int] = 2
SEATS_MOST: Final[int] = 6

SHEDDING_EVALUATION: Final[Evaluation] = Evaluation(
    ranks=RANK_SEQUENCE,
    suits=SUIT_SEQUENCE,
    wheel=False,
    wild_jokers=False,
    duplicates=Duplicates.COUNT,
)

SHEDDING_RANKING: Final[Ranking] = Ranking(
    patterns=tuple(SameRank(places=places) for places in range(SHED_LEAST, ALIKE_MOST + ONE_CARD)),
    evaluation=SHEDDING_EVALUATION,
)


def drawn_from(stock: int) -> Indices:
    """The position a draw takes, which is the card lying at the end of the stock.

    A stock of backs reads alike from either end, so this game draws from the end its players point at: an
    interface reads a heap by the last card of the run (`presentation.spread.Spread`), and that is the card a
    seat clicking the stock has picked out. The deal takes from the other end, which a shuffled pile is as
    indifferent to.

    Args:
        stock: how many cards the stock holds.

    Raises:
        LogicError: when the stock has run out, which leaves no card to draw.
    """
    if stock <= NO_CARDS:
        raise LogicError("A draw takes the card at the end of the stock, and the stock has run out")

    return frozenset({stock - ONE_CARD})


def may_act(hand: Sequence[CardOrJoker], stock: int) -> bool:
    """Whether a seat has a turn to take: a set in hand to shed, or a stock still holding a card to draw.

    Args:
        hand: the cards the seat holds.
        stock: how many cards the stock holds.
    """
    return stock > NO_CARDS or SHEDDING_RANKING.strongest(hand) is not None
