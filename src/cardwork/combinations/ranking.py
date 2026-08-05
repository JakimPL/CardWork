from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Annotated, Final, Self

from pydantic import Field, model_validator

from cardwork.cards.game import CardOrJoker
from cardwork.combinations.combination import BY_STRENGTH, ByReading, Combination
from cardwork.combinations.detect import find, selections
from cardwork.combinations.pattern import AnyPattern, Pattern
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.selection import Selection
from cardwork.models.base import BaseFrozen
from cardwork.ordering.composite import Composite
from cardwork.ordering.preorder import Key, Preorder
from cardwork.ordering.tiers import Tiers

ONE_PATTERN: Final[int] = 1
ABOVE: Final[int] = 1


class ByPattern(Preorder[Combination]):
    """Combinations by the pattern they answer, each taking the place the ranking gives that pattern."""

    def __init__(self, patterns: Sequence[Pattern]) -> None:
        self._patterns = Tiers(patterns)

    def key(self, value: Combination) -> Key:
        return self._patterns.key(value.pattern)


class Ranking(BaseFrozen):
    """The combinations a game recognises, weakest first, beside the reading it finds them by.

    A ranking reads cards and settles contests. `strongest` reads a run of cards into the best combination
    they hold, cards to spare being welcome, and `exactly` holds the run to a combination and all of it, which
    is what a play comes to. `order` states the strength relation itself, and being a preorder it carries
    `compare` for two combinations and `maxima` and `argmaxima` for a group of them, which is how several
    hands are settled against each other at once; `climbs` adds the clause a trick states, that a challenger
    takes as many cards as the combination it climbs over.

    Three readers answer what a table asks of the vocabulary it plays by. A trick is contested within a
    count, so `sizes` names the counts a combination takes and `sized` narrows the ranking to one of them.
    `ceilings` reads the strongest combination each count reaches out of a whole deck, which is what tells a
    table the best of a count has already been seen. `selections` reads a hand into every set of places that
    forms a combination, which is what a list of legal moves is made of.

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
        return Composite(
            ByPattern(self.patterns),
            BY_STRENGTH,
            ByReading(self.evaluation),
        )

    def sizes(self) -> tuple[int, ...]:
        """The counts a combination of this ranking takes, fewest first."""
        return tuple(sorted({pattern.size for pattern in self.patterns}))

    def sized(self, size: int) -> Ranking:
        """The ranking this one makes of the patterns taking that many cards, weakest first.

        A trick is contested within a count, so this is the ranking a seat answering one is held to. `sizes`
        names the counts a ranking answers for, which is what a game reads a count sent to it against.

        Raises:
            KeyError: when no pattern of this ranking takes that many cards.
        """
        taking = self._taking(size)
        if not taking:
            counts = ", ".join(str(count) for count in self.sizes())
            raise KeyError(f"No combination of this ranking takes {size} cards; it takes {counts}")

        return Ranking(patterns=taking, evaluation=self.evaluation)

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

    def exactly(self, cards: Iterable[CardOrJoker]) -> Combination | None:
        """The combination the cards are, every one of them taking a place in it, or None where they are none.

        `strongest` welcomes cards to spare, so four kings read there as the triplet a ranking listing one
        recognises. This holds the run to what it is, which is what a game admitting a combination and nothing
        besides asks of the cards a seat plays. The patterns are asked from the strongest downwards.
        """
        held = tuple(cards)
        for pattern in reversed(self.patterns):
            if pattern.size != len(held):
                continue

            found = find(held, pattern, self.evaluation)
            if found is not None:
                return found

        return None

    def climbs(self, challenger: Combination, held: Combination) -> bool:
        """Whether the challenger takes as many cards as the combination held and stands above it.

        A trick is contested within a count, so a combination of another count stands beside the one held
        rather than over it. Every contest is settled, since two combinations of one strength are separated by
        the cards they read, which is what `total_order` states.

        Raises:
            KeyError: when either combination answers a pattern this ranking leaves out.
        """
        if challenger.pattern.size != held.pattern.size:
            return False

        return self.total_order.compare(challenger, held) == ABOVE

    def ceilings(
        self,
        deck: Iterable[CardOrJoker],
    ) -> Mapping[int, Combination]:
        """The strongest combination each count reaches out of the whole deck, filed under the count it takes.

        A trick is contested within a count, so this states what a seat answering one cannot be climbed over:
        a game asking whether the table has already seen the best of a count reads it from here. The mapping
        names the counts the deck reaches.
        """
        held = tuple(deck)
        order = self.total_order
        reached: dict[int, Combination] = {}
        for size in self.sizes():
            found = self._reaching(held, size)
            if found:
                reached[size] = max(found, key=order.key)

        return reached

    def selections(
        self,
        cards: Sequence[CardOrJoker],
    ) -> tuple[Selection, ...]:
        """Every set of places in the run of cards that reads as a combination this ranking recognises.

        A move names the cards it plays by where they stand in the hand it was shown, so this is what a list of
        legal moves is made of: three kings offer their pair three ways, and the cards each of those leaves
        behind are what makes them three moves. The strongest patterns lead, and each set of places comes out
        once.
        """
        held = tuple(cards)
        return tuple(
            dict.fromkeys(
                selection
                for pattern in reversed(self.patterns)
                for selection in selections(held, pattern, self.evaluation)
            )
        )

    def _taking(self, size: int) -> tuple[Pattern, ...]:
        """The patterns taking that many cards, in the order this ranking places them."""
        return tuple(pattern for pattern in self.patterns if pattern.size == size)

    def _reaching(self, cards: Sequence[CardOrJoker], size: int) -> tuple[Combination, ...]:
        """The strongest instance of every pattern of that count the cards hold."""
        found = (find(cards, pattern, self.evaluation) for pattern in self._taking(size))
        return tuple(combination for combination in found if combination is not None)
