from collections.abc import Iterable
from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.orders import GERMAN_SUIT_SEQUENCE, RANK_SEQUENCE
from cardwork.combinations.combination import Combination
from cardwork.combinations.poker import (
    FLUSH,
    FULL_HOUSE,
    HIGH_CARD,
    PAIR,
    STRAIGHT,
    STRAIGHT_FLUSH,
    TRIPLET,
    TWO_PAIR,
)
from cardwork.combinations.policy import Duplicates, Evaluation
from cardwork.combinations.ranking import Ranking
from cardwork.exceptions import LogicError

SEATS_LEAST: Final[int] = 2
SEATS_MOST: Final[int] = 5

CLIMBING_PATTERNS = (
    HIGH_CARD,
    PAIR,
    TWO_PAIR,
    TRIPLET,
    STRAIGHT,
    FLUSH,
    FULL_HOUSE,
    STRAIGHT_FLUSH,
)

CLIMBING_EVALUATION = Evaluation(
    ranks=RANK_SEQUENCE,
    suits=GERMAN_SUIT_SEQUENCE,
    wheel=True,
    wild_jokers=False,
    duplicates=Duplicates.COLLAPSE,
)

CLIMBING_RANKING = Ranking(
    patterns=CLIMBING_PATTERNS,
    evaluation=CLIMBING_EVALUATION,
)

CLIMBING_ORDER = CLIMBING_RANKING.total_order


def combination_of(cards: Iterable[Card]) -> Combination:
    combination = CLIMBING_RANKING.strongest(cards)
    if combination is None:
        raise LogicError(f"Cards {cards} do not form a valid combination")

    return combination


def can_beat(combination: Combination, last_combination: Combination) -> bool:
    if len(combination.cards) != len(last_combination.cards):
        return False

    return CLIMBING_ORDER.compare(combination, last_combination) > 0
