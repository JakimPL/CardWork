from collections.abc import Iterable, Sequence
from typing import Annotated, Final, Self

from pydantic import Field, model_validator

from cardwork.cards.game import CardOrJoker
from cardwork.combinations.combination import BY_STRENGTH, ByReading, Combination
from cardwork.combinations.detect import find
from cardwork.combinations.pattern import AnyPattern, Pattern
from cardwork.combinations.policy import Evaluation
from cardwork.models.base import BaseFrozen
from cardwork.ordering.composite import Composite
from cardwork.ordering.preorder import Key, Preorder
from cardwork.ordering.tiers import Tiers

ONE_PATTERN: Final[int] = 1


class ByPattern(Preorder[Combination]):
    """Combinations by the pattern they answer, each taking the place the ranking gives that pattern."""

    def __init__(self, patterns: Sequence[Pattern]) -> None:
        self._patterns = Tiers(patterns)

    def key(self, value: Combination) -> Key:
        return self._patterns.key(value.pattern)


class Ranking(BaseFrozen):
    """The combinations a game recognises, weakest first, beside the reading it finds them by.

    A ranking answers two questions. `strongest` reads a run of cards and returns the best combination
    they form; `order` states the strength relation itself, and being a preorder it carries `compare` for
    two combinations and `maxima` and `argmaxima` for a group of them, which is how several hands are
    settled against each other at once.

    A pattern names the cards that make the combination, so the cards left beside it are the hand's own
    affair: a game that separates two equal pairs by the cards around them states that rule itself.
    """

    patterns: Annotated[tuple[AnyPattern, ...], Field(min_length=ONE_PATTERN)]
    evaluation: Evaluation

    @model_validator(mode="after")
    def _every_pattern_takes_one_place(self) -> Self:
        distinct = len(set(self.patterns))
        if distinct != len(self.patterns):
            raise ValueError(f"Every pattern takes one place, and {len(self.patterns)} of them fill {distinct}")

        return self

    @property
    def order(self) -> Preorder[Combination]:
        """Combinations by their pattern first and by their strength within it.

        Raises:
            KeyError: when a combination answers a pattern this ranking leaves out.
        """
        return Composite(ByPattern(self.patterns), BY_STRENGTH)

    @property
    def total_order(self) -> Preorder[Combination]:
        """Combinations by their pattern, by their strength within it, and then by the cards they read as.

        This refines `order` with the reading, so two combinations share a place exactly where they read as
        the same cards: single cards run by rank and then by suit, the pairs above them run the same way, and
        so on up the patterns. A game that needs one winner out of every contest asks here, and one that
        holds two pairs of kings equal asks `order`.

        One standard deck settles every contest this way. Several decks in play let one card be held twice,
        and two combinations reading the same cards stand alongside each other.

        Raises:
            KeyError: when a combination answers a pattern this ranking leaves out.
        """
        return Composite(ByPattern(self.patterns), BY_STRENGTH, ByReading(self.evaluation))

    def strongest(self, cards: Iterable[CardOrJoker]) -> Combination | None:
        """The best combination the cards form, or None where they form none the ranking recognises.

        The patterns are asked from the strongest downwards, so the first that answers is the answer.
        """
        held = tuple(cards)
        for pattern in reversed(self.patterns):
            found = find(held, pattern, self.evaluation)
            if found is not None:
                return found

        return None
