from collections.abc import Container
from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.game import CardOrJoker
from cardwork.combinations.assembly.filling import Filling
from cardwork.combinations.combination import Combination
from cardwork.combinations.demand import Demand
from cardwork.combinations.matching import UNPLACED, Matching
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.shape import Shape
from cardwork.combinations.tally import Tally
from cardwork.ordering.preorder import Key

type Standing = list[Card | None]

STRONGEST: Final[int] = 0


class Assembly:
    """One shape of a pattern, filled with what a hand offers it.

    `combination` answers with the strongest instance of that shape the cards make, or None where they fall
    short of it. The cards take as many places as they can hold at once, the strongest of them first, and a
    joker covers each place they leave open, so the shape stands as far as the jokers reach. A joker to spare
    then takes a place from the card standing there wherever that reads stronger by the pattern's own measure,
    which is what turns two spades and a joker into an ace-high flush.
    """

    def __init__(self, counted: Tally, pattern: Pattern, shape: Shape) -> None:
        self._counted = counted
        self._pattern = pattern
        self._shape = shape

    def combination(self) -> Combination | None:
        """The strongest combination this shape makes of the cards, or None where they fall short of it."""
        standing = self._matched()
        if standing is None:
            return None

        filling = self._read(self._improve(standing))
        return Combination(
            pattern=self._pattern,
            cards=filling.cards,
            reading=filling.reading,
            strength=self._strength(filling),
            low_ace=self._shape.low_ace,
        )

    def _matched(self) -> Standing | None:
        """The held card each place takes, and None at the places a joker stands for.

        Returns:
            The places as the cards fill them, and None for the whole shape where more places are left open
            than there are jokers to cover them.
        """
        admitted = tuple(
            tuple(place for place, demand in enumerate(self._shape.demands) if demand.admits(card))
            for card in self._counted.naturals
        )
        standing: Standing = [None] * self._shape.size
        for offer, place in enumerate(Matching(admitted, self._shape.size).placements):
            if place != UNPLACED:
                standing[place] = self._counted.naturals[offer]

        if standing.count(None) > len(self._counted.wilds):
            return None

        return standing

    def _improve(self, standing: Standing) -> Standing:
        """Where the places stand once every joker to spare has taken the place it reads strongest at."""
        spare = len(self._counted.wilds) - standing.count(None)
        while spare:
            stronger = self._stronger(standing)
            if stronger is None:
                return standing

            standing = stronger
            spare -= 1

        return standing

    def _stronger(self, standing: Standing) -> Standing | None:
        """Where one more joker outreads the card standing in its way, and None where none of them does.

        A joker to spare can only help by taking a place a card already holds, and which place that is the
        pattern alone can say: the joker that lifts a flush to ace-high leaves a pair of kings as it stands. So
        each place a card holds is offered to a joker in turn and the strongest reading of them all answers,
        which settles one joker and leaves the next to the same question.
        """
        reached = self._strength(self._read(standing))
        stronger: Standing | None = None
        for place, card in enumerate(standing):
            if card is None:
                continue

            offered: Standing = [*standing[:place], None, *standing[place + 1 :]]
            strength = self._strength(self._read(offered))
            if strength > reached:
                reached = strength
                stronger = offered

        return stronger

    def _read(self, standing: Standing) -> Filling:
        """The cards the places hold, beside what each reads as, a joker standing where a place is open."""
        cards: list[CardOrJoker] = []
        reading: list[Card] = []
        named = {card for card in standing if card is not None}
        wilds = iter(self._counted.wilds)
        for demand, card in zip(self._shape.demands, standing, strict=True):
            stands_for = card if card is not None else self._wild_reading(demand, named)
            named.add(stands_for)
            cards.append(card if card is not None else next(wilds))
            reading.append(stands_for)

        return Filling(cards=tuple(cards), reading=tuple(reading))

    def _wild_reading(self, demand: Demand, named: Container[Card]) -> Card:
        """What a joker stands for at this place: the strongest card the demand admits and the reading lacks.

        Where the reading already names every card the demand admits, the strongest of them stands again, which
        a flush longer than a suit is deep asks for.
        """
        candidates = demand.candidates(self._counted.evaluation)
        for card in candidates:
            if card not in named:
                return card

        return candidates[STRONGEST]

    def _strength(self, filling: Filling) -> Key:
        """Where the pattern places an instance reading this way."""
        return self._pattern.strength(filling.reading, self._counted.evaluation)
