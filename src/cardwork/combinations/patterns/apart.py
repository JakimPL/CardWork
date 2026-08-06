from collections.abc import Iterator
from dataclasses import replace
from typing import Literal, Self

from pydantic import model_validator

from cardwork.combinations.pattern import AnyPattern, Pattern, Reading
from cardwork.combinations.patterns.simple import ALIKE_PLACES
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.combinations.spread import Facet, Spread
from cardwork.ordering.preorder import Key


class Apart(Pattern):
    """The rule of another pattern, its places each taking a card, a rank or a suit of its own.

    Several decks in play let one card answer two places asking alike, so `SameRank(places=2)` reads the king
    of spades held twice as a pair. `Apart.of_suit(SameRank(places=2))` is the pair that holds two suits, and
    `Beside(parts=(that, that))` is two such pairs. `facet` states what the places hold apart: over one rank a
    card of one's own and a suit of one's own ask the same thing, and they part over two pair, where a card of
    one's own leaves the suits free and a suit of one's own asks for four.

    The rule stands as the part states it otherwise — the same places, the same strength, and the readings the
    part admits, each carrying one spread more. A spread multiplies no readings, so a pair holding two suits
    costs the thirteen readings a pair costs.
    """

    kind: Literal["apart"] = "apart"
    part: AnyPattern
    facet: Facet

    @classmethod
    def of_card(cls, part: Pattern) -> Self:
        """That rule with its places each taking a card of its own."""
        return cls(part=part, facet=Facet.CARD)

    @classmethod
    def of_rank(cls, part: Pattern) -> Self:
        """That rule with its places each taking a rank of its own."""
        return cls(part=part, facet=Facet.RANK)

    @classmethod
    def of_suit(cls, part: Pattern) -> Self:
        """That rule with its places each taking a suit of its own."""
        return cls(part=part, facet=Facet.SUIT)

    @model_validator(mode="after")
    def _the_places_stand_apart_from_each_other(self) -> Self:
        """Confirm the part holds places a spread reads over, and holds none of them apart already.

        Raises:
            ValueError: when the part takes fewer than two places, which one card reads apart from nothing at,
                or when the part holds places apart already, which leaves them holding apart twice.
        """
        if self.part.size < ALIKE_PLACES:
            raise ValueError(
                f"Places read apart from {ALIKE_PLACES} of them upwards, and this rule takes {self.part.size}"
            )

        if self.part.spread:
            raise ValueError(f"A place reads apart one way, and {self.part} holds places apart already")

        return self

    @model_validator(mode="after")
    def _the_places_read_apart_ask_alike(self) -> Self:
        """Confirm a spread by rank or by suit reads over places asking alike.

        Where the places ask alike, every card showing one facing answers every one of them, and the filling
        settles which card takes which place. Where they ask differently, one facing answers some of the places
        and not others, and which cards a reading holds is settled by more than the filling can read.

        Raises:
            ValueError: when a spread by rank or by suit reads over places asking differently.
        """
        if self.facet is not Facet.CARD and not self.part.alike:
            raise ValueError(
                f"A spread by {self.facet.value} reads over places asking alike, and {self.part} asks "
                f"differently of them; hold each of its parts apart instead, or read them apart by card"
            )

        return self

    @property
    def size(self) -> int:
        return self.part.size

    @property
    def alike(self) -> bool:
        return self.part.alike

    @property
    def spread(self) -> bool:
        return True

    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        for shape in self.part.shapes(evaluation):
            yield replace(shape, spreads=(*shape.spreads, self._spread(shape.size)))

    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        return self.part.strength(reading, evaluation)

    def __str__(self) -> str:
        return f"{self.part} apart by {self.facet.value}"

    def _spread(self, size: int) -> Spread:
        """The places of a reading this rule holds apart, which are all of them."""
        return Spread(facet=self.facet, places=frozenset(range(size)))
