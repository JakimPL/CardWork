from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.combinations.demand import Demand


@dataclass(frozen=True)
class Shape:
    """One reading a pattern admits, stated as what each of its places asks for.

    A pattern lists its shapes and the search fills them, so this is the whole of what a rule states about
    its content: the pair of kings is two places asking for a king, and a spade flush is five places asking
    for a spade. `together` and `beside` build the shapes of a pattern made of parts.

    `low_ace` marks the reading where a run begins on the highest rank and continues from the lowest, so that
    the combination built from it knows the ace stands for one.
    """

    demands: tuple[Demand, ...]
    low_ace: bool

    @classmethod
    def together(cls, shapes: Sequence[Shape]) -> Shape | None:
        """The one reading that asks what every one of these asks, place by place.

        Returns:
            The shared reading, and None where a place is left asking for two ranks or two suits at once,
            which is what a run of one suit read together with a flush of another comes to.
        """
        demands: list[Demand] = []
        for standing in zip(*(shape.demands for shape in shapes), strict=True):
            shared = cls._shared(standing)
            if shared is None:
                return None

            demands.append(shared)

        return cls(demands=tuple(demands), low_ace=cls._low_ace(shapes))

    @classmethod
    def beside(cls, shapes: Sequence[Shape]) -> Shape:
        """One reading holding the places of every one of these, in the order they are given."""
        return cls(
            demands=tuple(demand for shape in shapes for demand in shape.demands),
            low_ace=cls._low_ace(shapes),
        )

    @staticmethod
    def apart(shapes: Sequence[Shape]) -> bool:
        """Whether these readings each keep ranks and suits of their own, naming none that another names."""
        return Shape._spread([shape.ranks for shape in shapes]) and Shape._spread([shape.suits for shape in shapes])

    @property
    def size(self) -> int:
        """How many places the reading fills."""
        return len(self.demands)

    @property
    def ranks(self) -> frozenset[Rank]:
        """The ranks this reading names."""
        return frozenset(demand.rank for demand in self.demands if demand.rank is not None)

    @property
    def suits(self) -> frozenset[Suit]:
        """The suits this reading names."""
        return frozenset(demand.suit for demand in self.demands if demand.suit is not None)

    @staticmethod
    def _shared(standing: Sequence[Demand]) -> Demand | None:
        """What every demand standing on one place asks of it together."""
        shared = standing[0]
        for coming in standing[1:]:
            met = shared.meet(coming)
            if met is None:
                return None

            shared = met

        return shared

    @staticmethod
    def _spread[ValueT](named: Sequence[frozenset[ValueT]]) -> bool:
        """Whether the named values are spread over the sets, each of them appearing in one set alone."""
        return len(frozenset[ValueT]().union(*named)) == sum(len(values) for values in named)

    @staticmethod
    def _low_ace(shapes: Sequence[Shape]) -> bool:
        """Whether any of these readings takes its highest rank as its lowest."""
        return any(shape.low_ace for shape in shapes)
