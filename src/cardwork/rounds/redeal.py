from collections.abc import Callable, Mapping
from random import Random
from typing import Final, Generic

from cardwork.decks.draw import permutation
from cardwork.effects.effects import Effects, MoveCards, Reorder, SetFace
from cardwork.effects.fold import fold
from cardwork.positions.position import Position
from cardwork.states.state import GameState, StateT
from cardwork.zones.zone import ZoneId

DRAWS_MOST: Final[int] = 1000

type Admits[S: GameState] = Callable[[Position[S]], bool]


class Redeal(Generic[StateT]):
    """The deal of a fresh round, made out of the cards the last one left where they lay.

    Every card comes back to one pile, the pile is shuffled, and the hands are dealt off the top of it, which
    is the whole of what a round boundary does to the table:

        Redeal(position, pile="pile", face_down=True).effects(counts={"hand:0": 5, "hand:1": 5}, rng=rng)

    `counts` states how many cards each zone is owed, and they leave the pile in the order it names them, so a
    game deals round the table from its leader by stating the zones in that order. The three steps stand on
    their own for a game that keeps part of the table standing between rounds.

    `admitted` deals what a game asks of the round it opens on, drawing again for as long as a draw is refused.
    """

    def __init__(self, position: Position[StateT], pile: ZoneId, *, face_down: bool) -> None:
        self._position = position
        self._pile = pile
        self._face_down = face_down

    def effects(self, counts: Mapping[ZoneId, int], rng: Random) -> Effects[StateT]:
        """Every card gathered into the pile, the pile shuffled, and each zone dealt the count it is owed."""
        return self.gather() + self.shuffle(rng) + self.distribute(counts)

    def admitted(
        self,
        counts: Mapping[ZoneId, int],
        rng: Random,
        admits: Admits[StateT],
    ) -> Effects[StateT]:
        """The first deal the game admits, drawn afresh for as long as a draw is refused.

        A game that asks something of the round it opens on states it here: a seat holding a hand still to be
        played for, a hand with a move to make in it. Each draw is a shuffle of the whole pile, which is what
        leaves the deal that is kept standing uniformly among the deals the game admits: every one of them is
        as likely as every other, and no card is favoured beyond what was asked for.

        The accepted draw alone becomes effects, and the order it settles on is what the journal keeps, so a
        replay deals the same round and a run of the same seed reaches the same table.

        Args:
            counts: how many cards each zone is owed, in the order the deal hands them out.
            rng: the generator each draw comes from.
            admits: whether the table a draw lays out is one the round opens on.

        Raises:
            ValueError: when `DRAWS_MOST` draws pass with every one refused, which is where a game asking for a
                deal its deck holds none of is answered.
        """
        for _ in range(DRAWS_MOST):
            drawn = self.effects(counts, rng)
            if admits(fold(drawn, self._position)):
                return drawn

        raise ValueError(f"No deal of {dict(counts)} was admitted in {DRAWS_MOST} draws")

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

        return (
            SetFace(
                zone=self._pile,
                indices=turning,
                face_down=self._face_down,
            ),
        )

    def _emptied(self) -> Effects[StateT]:
        """Every zone besides the pile that holds a card, emptied into it."""
        return tuple(
            MoveCards(
                source=zone_id,
                indices=frozenset(range(len(zone.cards))),
                target=self._pile,
                face_down=self._face_down,
            )
            for zone_id, zone in sorted(self._position.board.zones.items())
            if zone.cards and zone_id != self._pile
        )

    def shuffle(self, rng: Random) -> Effects[StateT]:
        """The gathered pile laid out in an order drawn once and recorded, so a replay deals the same round."""
        return (Reorder(zone=self._pile, order=permutation(self._gathered(), rng)),)

    def distribute(self, counts: Mapping[ZoneId, int]) -> Effects[StateT]:
        """The top of the pile dealt out, each zone taking its count in the order the counts name them."""
        return tuple(
            MoveCards(
                source=self._pile,
                indices=frozenset(range(count)),
                target=zone_id,
                face_down=self._face_down,
            )
            for zone_id, count in counts.items()
            if count
        )

    def _gathered(self) -> int:
        """How many cards the pile holds once every zone has emptied into it."""
        return sum(len(zone.cards) for zone in self._position.board.zones.values())
