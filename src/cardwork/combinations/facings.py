from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Self

from cardwork.cards.card import Card, Facing
from cardwork.cards.game import CardOrJoker
from cardwork.combinations.demand import Demand
from cardwork.combinations.policy import Evaluation
from cardwork.combinations.spread import Spread


@dataclass(frozen=True)
class Facings:
    """What the places of each spread have taken as a selection is picked, group by group.

    A spread holds its places to facings of their own, so the cards picked into one show facings apart from each
    other and a joker there reads as a card showing a facing they leave free. `taken` are the facings the cards
    show, held apart as each group is picked; `jokers` are the demands the jokers stand at, which are answered
    once every card is picked, the order the filling reads them in: the cards take the places they answer and
    the jokers cover the places left open.
    """

    taken: Mapping[Spread, frozenset[Facing]]
    jokers: Mapping[Spread, tuple[Demand, ...]]

    @classmethod
    def free(cls) -> Self:
        """Where nothing is picked yet, which leaves every facing of every spread free."""
        return cls(taken={}, jokers={})

    def picking(
        self,
        spread: Spread | None,
        demand: Demand,
        picked: Sequence[CardOrJoker],
    ) -> Facings | None:
        """What the spreads have taken once these cards answer places of that spread asking that demand.

        Places reading apart in no spread take the cards they are given, which leaves the facings as they stand.

        Returns:
            The facings taken, and None where two of the cards show one facing of that spread or one shows a
            facing the spread has taken already, which is what a card held twice comes to in a pair read apart
            by suit.
        """
        if spread is None:
            return self

        cards = tuple(card for card in picked if isinstance(card, Card))
        showing = frozenset(spread.read(card) for card in cards)
        held = self.taken.get(spread, frozenset())
        if len(showing) != len(cards) or not showing.isdisjoint(held):
            return None

        standing = tuple(demand for card in picked if not isinstance(card, Card))
        return Facings(
            taken={**self.taken, spread: held | showing},
            jokers={
                **self.jokers,
                spread: (
                    *self.jokers.get(spread, ()),
                    *standing,
                ),
            },
        )

    def reads(self, evaluation: Evaluation) -> bool:
        """Whether every joker standing in a spread reads as a card showing a facing of its own."""
        return all(self._stands(spread, evaluation) for spread in self.jokers)

    def _stands(self, spread: Spread, evaluation: Evaluation) -> bool:
        """Whether the jokers of that spread each read as a card showing what the cards and the others leave.

        Each joker takes the facing of the strongest card its demand admits that the spread leaves free, and the
        jokers after it read apart from that, so four suits leave the fifth place of a rank read apart by suit
        standing empty.
        """
        held = set(self.taken.get(spread, frozenset()))
        for demand in self.jokers[spread]:
            shown = next(
                (
                    facing
                    for facing in self._showing(
                        spread,
                        demand,
                        evaluation,
                    )
                    if facing not in held
                ),
                None,
            )
            if shown is None:
                return False

            held.add(shown)

        return True

    @staticmethod
    def _showing(
        spread: Spread,
        demand: Demand,
        evaluation: Evaluation,
    ) -> Iterator[Facing]:
        """The facings a card answering that demand shows, read from the strongest card of the deck downwards."""
        return (spread.read(card) for card in demand.candidates(evaluation))
