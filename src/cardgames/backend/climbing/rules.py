from typing import Final

from cardwork.cards.orders import GERMAN_SUIT_SEQUENCE, RANK_SEQUENCE
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.poker import (
    FLUSH,
    FULL_HOUSE,
    HIGH_CARD,
    PAIR,
    STRAIGHT,
    STRAIGHT_FLUSH,
    TRIPLET,
)
from cardwork.combinations.policy import Duplicates, Evaluation
from cardwork.combinations.ranking import Ranking
from cardwork.states.award import Award

SEATS_LEAST: Final[int] = 2
SEATS_MOST: Final[int] = 5
AWARD: Final[Award] = Award.HIGHEST

CLIMBING_PATTERNS: Final[tuple[Pattern, ...]] = (
    HIGH_CARD,
    PAIR,
    TRIPLET,
    STRAIGHT,
    FLUSH,
    FULL_HOUSE,
    STRAIGHT_FLUSH,
)

CLIMBING_EVALUATION: Final[Evaluation] = Evaluation(
    ranks=RANK_SEQUENCE,
    suits=GERMAN_SUIT_SEQUENCE,
    wheel=True,
    wild_jokers=False,
    duplicates=Duplicates.COLLAPSE,
)

CLIMBING_RANKING: Final[Ranking] = Ranking(
    patterns=CLIMBING_PATTERNS,
    evaluation=CLIMBING_EVALUATION,
)
