from collections.abc import Mapping
from random import Random
from typing import Generic

from cardwork.decks.draw import permutation
from cardwork.effects.effects import Effects, MoveCards, Reorder, SetFace
from cardwork.positions.position import Position
from cardwork.states.state import StateT
from cardwork.zones.zone import ZoneId


class Redeal(Generic[StateT]):
    """The deal of a fresh round, made out of the cards the last one left where they lay.

    Every card comes back to one pile, the pile is shuffled, and the hands are dealt off the top of it, which
    is the whole of what a round boundary does to the table:

        Redeal(position, pile="pile", face_down=True).effects(counts={"hand:0": 5, "hand:1": 5}, rng=rng)

    `counts` states how many cards each zone is owed, and they leave the pile in the order it names them, so a
    game deals round the table from its leader by stating the zones in that order. The three steps stand on
    their own for a game that keeps part of the table standing between rounds.
    """

    def __init__(self, position: Position[StateT], pile: ZoneId, *, face_down: bool) -> None:
        self._position = position
        self._pile = pile
        self._face_down = face_down

    def effects(self, counts: Mapping[ZoneId, int], rng: Random) -> Effects[StateT]:
        """Every card gathered into the pile, the pile shuffled, and each zone dealt the count it is owed."""
        return self.gather() + self.shuffle(rng) + self.distribute(counts)

    def gather(self) -> Effects[StateT]:
        """Every card on the table back into the pile at one face, zone by zone in the order their names sort.

        Sorting settles the arrangement the pile comes to hold, which is what leaves the shuffle that follows
        the only thing deciding where a card ends up.
        """
        return self._turned() + self._emptied()

    def _turned(self) -> Effects[StateT]:
        """The cards the pile already holds brought to the face the gathered ones arrive at.

        Only the cards that do turn are named, so a pile already lying at that face asks for nothing.
        """
        held = self._position.board.zone(self._pile).cards
        turning = frozenset(place for place, card in enumerate(held) if card.face_down != self._face_down)
        if not turning:
            return ()

        turned: Effects[StateT] = (
            SetFace(
                zone=self._pile,
                indices=turning,
                face_down=self._face_down,
            ),
        )
        return turned

    def _emptied(self) -> Effects[StateT]:
        """Every zone besides the pile that holds a card, emptied into it."""
        emptied: Effects[StateT] = tuple(
            MoveCards(
                source=zone_id,
                indices=frozenset(range(len(zone.cards))),
                target=self._pile,
                face_down=self._face_down,
            )
            for zone_id, zone in sorted(self._position.board.zones.items())
            if zone.cards and zone_id != self._pile
        )

        return emptied

    def shuffle(self, rng: Random) -> Effects[StateT]:
        """The gathered pile laid out in an order drawn once and recorded, so a replay deals the same round."""
        shuffled: Effects[StateT] = (Reorder(zone=self._pile, order=permutation(self._gathered(), rng)),)
        return shuffled

    def distribute(self, counts: Mapping[ZoneId, int]) -> Effects[StateT]:
        """The top of the pile dealt out, each zone taking its count in the order the counts name them."""
        dealt: Effects[StateT] = tuple(
            MoveCards(
                source=self._pile,
                indices=frozenset(range(count)),
                target=zone_id,
                face_down=self._face_down,
            )
            for zone_id, count in counts.items()
            if count
        )

        return dealt

    def _gathered(self) -> int:
        """How many cards the pile holds once every zone has emptied into it."""
        return sum(len(zone.cards) for zone in self._position.board.zones.values())
