from collections.abc import Iterator, Sequence

from cardwork.combinations.pattern import Pattern, Reading
from cardwork.combinations.patterns.compound import Compound
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.shape import Shape
from cardwork.ordering.preorder import Key


class Beside(Compound):
    """The places of every part, one after another, each part keeping ranks and suits of its own.

    Two pair is a pair beside a pair and a full house is three of a rank beside two, and what makes either of
    them more than four or five of one rank is that a part leaves the ranks and suits another part names to it.
    An instance is settled by the parts in the order they are named, so a full house leads with its triplet, and
    a pair beside three loose places is settled by the pair and then by the cards standing around it.
    """

    @property
    def size(self) -> int:
        return sum(part.size for part in self.parts)

    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        listings = self._listings(evaluation)
        for chosen in self._choices(listings):
            if self._listed(chosen):
                taken = self._taken(listings, chosen)
                if Shape.apart(taken):
                    yield Shape.beside(taken)

    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        return tuple(place for part, portion in self._portions(reading) for place in part.strength(portion, evaluation))

    def __str__(self) -> str:
        return " beside ".join(str(part) for part in self.parts)

    def _portions(self, reading: Reading) -> Iterator[tuple[Pattern, Reading]]:
        """What each part reads out of the whole, in the order the parts take their places."""
        taken = 0
        for part in self.parts:
            yield part, reading[taken : taken + part.size]
            taken += part.size

    def _listed(self, chosen: Sequence[int]) -> bool:
        """Whether parts reading alike take their readings in the order the pattern lists them.

        Parts that read alike are interchangeable, so holding them to the order they are listed in counts each
        selection once: the pair of kings beside the pair of queens is the reading, and the queens beside the
        kings are that same reading read backwards.
        """
        return all(
            chosen[place] <= chosen[place + 1]
            for place in range(len(self.parts) - 1)
            if self.parts[place] == self.parts[place + 1]
        )
