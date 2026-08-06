from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations
from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.game import CardOrJoker
from cardwork.combinations.demand import Demand
from cardwork.combinations.facings import Facings
from cardwork.combinations.policy import Duplicates, Evaluation
from cardwork.combinations.shape import Shape
from cardwork.combinations.spread import Spread

type Selection = frozenset[int]

FIRST_GROUP: Final[int] = 0


@dataclass(frozen=True)
class Asking:
    """One demand a shape makes of the places of one spread, beside how many of those places make it.

    Places asking alike within one spread are answered as a group, which counts a choice of cards once rather
    than once per order of them. The spread comes with the demand, so the cards picked into a group are held to
    facings of their own where the places of that group read apart.
    """

    demand: Demand
    spread: Spread | None
    places: int


class Selecting:
    """One shape and every selection a run of cards offers it, one card answering each demand it makes.

    `Assembly` reads a run of cards into the strongest instance of a shape; this reads the same shape into
    every selection the cards offer it, stated as the places they stand at. Three kings hold one pair of kings
    and offer it three ways, and the cards each of those leaves behind are what makes them three moves rather
    than one.

    Demands asking alike are answered together, so a suit five places deep is a choice of five cards rather
    than an order of them, and a joker free to stand in answers whatever a demand asks. Places the shape holds
    apart are answered by cards showing facings of their own, so a king of spades held twice answers one place
    of a pair read apart by suit between the two copies.
    """

    def __init__(
        self,
        cards: Sequence[CardOrJoker],
        shape: Shape,
        evaluation: Evaluation,
    ) -> None:
        self._cards = cards
        self._shape = shape
        self._evaluation = evaluation
        self._admitted = self._admitting()
        self._asked = self._grouped()

    @property
    def selections(self) -> tuple[Selection, ...]:
        """Every set of places whose cards fill this shape, each of them named once."""
        chosen = self._chosen(FIRST_GROUP, frozenset(), Facings.free())
        taken = (selection for selection in chosen if self._reads_apart(selection))
        return tuple(dict.fromkeys(taken))

    def _admitting(self) -> Mapping[Demand, tuple[int, ...]]:
        """The places of the run answering each demand this shape makes."""
        return {
            demand: tuple(place for place, card in enumerate(self._cards) if self._answers(demand, card))
            for demand in self._shape.demands
        }

    def _answers(self, demand: Demand, card: CardOrJoker) -> bool:
        """Whether the card standing at a place of the run answers that demand, a wild joker answering any."""
        if isinstance(card, Card):
            return demand.admits(card)

        return self._evaluation.wild_jokers

    def _grouped(self) -> tuple[Asking, ...]:
        """Each demand this shape makes of the places of one spread, the narrowest of the groups leading.

        Demands asking alike within one spread are answered as one group, which counts a choice of cards once
        rather than once per order of them. Leading with the group the fewest cards answer settles a shape the
        run falls short of in one step.
        """
        asked = Counter(
            zip(
                self._shape.demands,
                self._shape.spreading(),
                strict=True,
            )
        )
        groups = (Asking(demand=demand, spread=spread, places=places) for (demand, spread), places in asked.items())
        return tuple(sorted(groups, key=self._answering))

    def _answering(self, asked: Asking) -> int:
        """How many places of the run answer the demand this group asks."""
        return len(self._admitted[asked.demand])

    def _chosen(
        self,
        group: int,
        taken: Selection,
        facings: Facings,
    ) -> Iterator[Selection]:
        """Every way the groups from this one onwards are answered out of the places the run has left.

        A group whose places read apart takes cards showing facings of their own, and the jokers picked into one
        answer once every card is picked: a way stands where each of its jokers reads as a card showing a facing
        the cards picked leave free.
        """
        if group == len(self._asked):
            if facings.reads(self._evaluation):
                yield taken

            return

        asked = self._asked[group]
        free = tuple(place for place in self._admitted[asked.demand] if place not in taken)
        for picked in combinations(free, asked.places):
            showing = facings.picking(asked.spread, asked.demand, self._standing(picked))
            if showing is not None:
                yield from self._chosen(group + 1, taken | frozenset(picked), showing)

    def _standing(self, picked: Sequence[int]) -> tuple[CardOrJoker, ...]:
        """The cards standing at those places of the run."""
        return tuple(self._cards[place] for place in picked)

    def _reads_apart(self, taken: Selection) -> bool:
        """Whether the selection reads as as many cards as it takes, which a reading collapsing repeats asks.

        Under `COUNT` each card answers for itself, so every selection stands. Under `COLLAPSE` a card held
        twice reads once, which leaves one card to answer the two demands a selection holding it twice fills.
        """
        if self._evaluation.duplicates is Duplicates.COUNT:
            return True

        held = tuple(self._cards[place] for place in taken)
        return len(set(held)) == len(held)
