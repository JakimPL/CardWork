from collections.abc import Iterable
from typing import Final

from cardwork.cards.game import CardOrJoker
from cardwork.cards.orders import RANK_SEQUENCE, SUIT_SEQUENCE
from cardwork.combinations.detect import contains, matches
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.patterns.same_rank import SameRank
from cardwork.combinations.patterns.same_suit import SameSuit
from cardwork.combinations.policy import Duplicates, Evaluation
from cardwork.states.award import Award

HAND_SIZE: Final[int] = 3
HAND_ON_TURN: Final[int] = HAND_SIZE + 1
THREE_ALIKE: Final[int] = 3
AWARD: Final[Award] = Award.HIGHEST
ROUND_POINT: Final[int] = 1
NOTHING: Final[int] = 0

PASSING_EVALUATION: Final[Evaluation] = Evaluation(
    ranks=RANK_SEQUENCE,
    suits=SUIT_SEQUENCE,
    wheel=False,
    wild_jokers=True,
    duplicates=Duplicates.COUNT,
)

DECLARING_PATTERNS: Final[tuple[Pattern, ...]] = (
    SameRank(places=THREE_ALIKE),
    SameSuit(places=THREE_ALIKE),
)
WITHHOLDING_PATTERNS: Final[tuple[Pattern, ...]] = (
    SameRank(places=HAND_ON_TURN),
    SameSuit(places=HAND_ON_TURN),
)


def three_read_alike(hand: Iterable[CardOrJoker]) -> bool:
    """Whether some three of the cards read as one rank or as one suit, a joker standing in for either."""
    held = tuple(hand)
    return any(contains(held, pattern, PASSING_EVALUATION) for pattern in DECLARING_PATTERNS)


def four_read_alike(hand: Iterable[CardOrJoker]) -> bool:
    """Whether all four of the cards read as one rank or as one suit, which is what holds a win back."""
    held = tuple(hand)
    return any(matches(held, pattern, PASSING_EVALUATION) for pattern in WITHHOLDING_PATTERNS)


def declares(hand: Iterable[CardOrJoker]) -> bool:
    """Whether a hand of four wins: some three of it read alike in rank or in suit, while the four do not.

    A joker stands in for whatever the three asks of it, and that one rule settles every hand a joker reaches:
    a joker left spare joins the other three in reading alike, and the four alike hold the win back. So every
    joker a winning hand holds sits inside the three, which follows from the rule rather than standing beside
    it, and three jokers or four leave the four reading alike whatever the rest of the hand is.

    Cards from different decks count as themselves, so three spade cards are three of a suit where two of them
    are the same spade.
    """
    held = tuple(hand)
    return len(held) == HAND_ON_TURN and three_read_alike(held) and not four_read_alike(held)
