from collections.abc import Iterator
from typing import Final, Literal, Self

from pydantic import model_validator

from cardwork.combinations.pattern import Reading
from cardwork.combinations.patterns.compound import Compound
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.ordering.preorder import Key

LEADING_PART: Final[int] = 0
ONE_PART: Final[int] = 1


class Together(Compound):
    """One set of places every part reads at once, which is what a suited run of five states.

    Each place asks what all the parts ask of it, so a run read together with a flush asks each of its places
    for one card: the rank the run reaches there, in the suit the flush holds. Every part reads the same number
    of places, and an instance is settled by the parts in the order they are named.
    """

    kind: Literal["together"] = "together"

    @model_validator(mode="after")
    def _every_part_reads_the_same_places(self) -> Self:
        asked = sorted({part.size for part in self.parts})
        if len(asked) != 1:
            raise ValueError(f"Parts read one set of places together, and these ask for {asked} places")

        return self

    @model_validator(mode="after")
    def _one_part_holds_the_places_apart(self) -> Self:
        """Confirm the parts leave the places reading apart one way.

        Raises:
            ValueError: when two parts hold places apart, which leaves the shared places holding apart twice.
        """
        holding = tuple(str(part) for part in self.parts if part.spread)
        if len(holding) > ONE_PART:
            raise ValueError(f"Places read apart one way, and these parts each hold them apart: {holding}")

        return self

    @property
    def size(self) -> int:
        return self.parts[LEADING_PART].size

    @property
    def alike(self) -> bool:
        return all(part.alike for part in self.parts)

    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        listings = self._listings(evaluation)
        for chosen in self._choices(listings):
            shared = Shape.together(self._taken(listings, chosen))
            if shared is not None:
                yield shared

    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        return tuple(
            place
            for part in self.parts
            for place in part.strength(
                reading,
                evaluation,
            )
        )

    def __str__(self) -> str:
        return " together with ".join(str(part) for part in self.parts)
