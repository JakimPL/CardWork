from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.game import CardsOrJokers
from cardwork.combinations.assembly.filling import Filling
from cardwork.combinations.assembly.naming import Naming
from cardwork.combinations.assembly.seating import Seating
from cardwork.combinations.combination import Combination
from cardwork.combinations.matching import UNPLACED, Matching
from cardwork.combinations.pattern import Pattern, Reading
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

    Places the shape holds apart take cards facing apart: the cards reach them through gates the matching seats
    one card at a time, and a joker there reads as a card whose facing its spread leaves free. The shape falls
    short where those facings run out, which is what four suits do to five of a rank read apart by suit.
    """

    def __init__(self, counted: Tally, pattern: Pattern, shape: Shape) -> None:
        self._counted = counted
        self._pattern = pattern
        self._shape = shape
        self._spreading = shape.spreading()

    def combination(self) -> Combination | None:
        """The strongest combination this shape makes of the cards, or None where they fall short of it."""
        standing = self._matched()
        if standing is None:
            return None

        filling = self._read(self._improve(standing))
        if filling is None:
            return None

        return Combination(
            pattern=self._pattern,
            cards=filling.cards,
            reading=filling.reading,
            strength=self._pattern.strength(filling.reading, self._counted.evaluation),
            low_ace=self._shape.low_ace,
        )

    def _matched(self) -> Standing | None:
        """The held card each place takes, and None at the places a joker stands for.

        Returns:
            The places as the cards fill them, and None for the whole shape where more places are left open
            than there are jokers to cover them.
        """
        seating = Seating.of(self._counted.naturals, self._shape, self._spreading)
        standing: Standing = [None] * self._shape.size
        for offer, place in enumerate(Matching(seating.seats, self._shape.size, seating.gates).placements):
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
        reached = self._strength(standing)
        stronger: Standing | None = None
        for place, card in enumerate(standing):
            if card is None:
                continue

            offered: Standing = [*standing[:place], None, *standing[place + 1 :]]
            strength = self._strength(offered)
            if strength is not None and (reached is None or strength > reached):
                reached = strength
                stronger = offered

        return stronger

    def _read(self, standing: Standing) -> Filling | None:
        """The cards the places hold, beside what each of them reads as.

        Returns:
            The filling, and None where a joker stands at a place the reading leaves nothing to stand for.
        """
        reading = self._reading(standing)
        if reading is None:
            return None

        return Filling(cards=self._holding(standing), reading=reading)

    def _holding(self, standing: Standing) -> CardsOrJokers:
        """The cards the places came to hold, a joker standing where the held cards left a place open."""
        wilds = iter(self._counted.wilds)
        return tuple(card if card is not None else next(wilds) for card in standing)

    def _reading(self, standing: Standing) -> Reading | None:
        """What each place reads as: the card holding it, or what the joker at an open place stands for.

        Each joker read joins the naming, so the one after it reads apart from what it stands for.

        Returns:
            The reading, and None where a place reading apart is left no card its joker can stand for, which is
            what four suits do to five of a rank read apart by suit.
        """
        naming = Naming.of(standing, self._spreading)
        reading: list[Card] = []
        for place, card in enumerate(standing):
            if card is not None:
                reading.append(card)
                continue

            stands_for = self._wild_reading(place, naming)
            if stands_for is None:
                return None

            naming.take(place, stands_for)
            reading.append(stands_for)

        return tuple(reading)

    def _wild_reading(self, place: int, naming: Naming) -> Card | None:
        """What a joker stands for at this place: the strongest card the demand admits and the naming leaves.

        Where the naming leaves none of them free and the place reads apart in nothing, the strongest card the
        demand admits stands again, which a flush longer than a suit is deep asks for.

        Returns:
            The card the joker reads as, and None where the place reads apart in a spread and every card the
            demand admits either stands in the reading already or faces as one of that spread's places does.
        """
        candidates = self._shape.demands[place].candidates(self._counted.evaluation)
        free = next((card for card in candidates if naming.leaves(place, card)), None)
        if free is not None:
            return free

        if self._spreading[place] is None:
            return candidates[STRONGEST]

        return None

    def _strength(self, standing: Standing) -> Key | None:
        """Where the pattern places an instance standing this way, and None where it reads as none."""
        filling = self._read(standing)
        if filling is None:
            return None

        return self._pattern.strength(filling.reading, self._counted.evaluation)
