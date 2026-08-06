from collections.abc import Sequence
from typing import Final

type Seat = tuple[int, int]

UNPLACED: Final[int] = -1


class Matching:
    """Offers and the seats they answer, each offer taking a seat of its own.

    A seat is a place beside the gate an offer passes through to reach it, and a gate seats one offer at a
    time: the places a spread holds apart share a gate for every facing, so two cards facing alike answer one
    place of that spread between them. A place reading apart in no spread is reached through a gate of its own,
    which leaves the place the whole of what it asks. `admitted[offer]` lists the seats that offer answers, and
    `placements` states the place each offer took.

    Two properties carry the search that reads a hand into a combination: as many places are filled as any
    assignment could fill, and among the assignments filling that many, the offers standing earliest are the
    ones placed — so reading a hand from its strongest card downwards fills a combination with the strongest
    cards it can hold. They hold of the seatings `Seating` states, where an offer reaches a place through one
    gate and the gates a spread keeps stand behind that spread alone.
    """

    def __init__(
        self,
        admitted: Sequence[Sequence[Seat]],
        places: int,
        gates: int,
    ) -> None:
        self._admitted = admitted
        self._at: list[int] = [UNPLACED] * places
        self._through: list[int] = [UNPLACED] * gates
        self._taken: list[int] = [UNPLACED] * len(admitted)
        self._gated: list[int] = [UNPLACED] * len(admitted)
        for offer in range(len(admitted)):
            self._place(offer, set(), set())

    @property
    def placements(self) -> tuple[int, ...]:
        """The place each offer took, holding `UNPLACED` for an offer that answers held seats alone."""
        return tuple(self._taken)

    def _place(self, offer: int, places: set[int], gates: set[int]) -> bool:
        """Find this offer a seat and say whether one was found.

        A seat standing open goes to the offer directly, and what the offer itself holds stands open to it, so
        an offer moving on keeps the gate it passes and takes a place behind it. Where every seat it answers is
        held, the offer asks the holder of each in turn to move on and takes the seat of the first holder that
        finds another, so that one chain of moves reaches every seat such a rearrangement opens. The places and
        the gates a chain has promised stay promised, which is what settles it. A seat whose place one offer
        holds and whose gate another holds stays with them, since seating this offer there would move two
        offers on to seat one.
        """
        for place, gate in self._admitted[offer]:
            if place in places or gate in gates:
                continue

            if self._free(place, offer) and self._open(gate, offer):
                self._hold(offer, place, gate)
                return True

        for place, gate in self._admitted[offer]:
            if place in places or gate in gates:
                continue

            moving = self._holder(place, gate)
            if moving == UNPLACED:
                continue

            places.add(place)
            gates.add(gate)
            left, passed = self._taken[moving], self._gated[moving]
            if self._place(moving, places, gates):
                self._release(moving, left, passed)
                self._hold(offer, place, gate)
                return True

        return False

    def _free(self, place: int, offer: int) -> bool:
        """Whether the place stands open to this offer, which the place it holds itself does."""
        return self._at[place] in (UNPLACED, offer)

    def _open(self, gate: int, offer: int) -> bool:
        """Whether the gate stands open to this offer, which the gate it passes itself does."""
        return self._through[gate] in (UNPLACED, offer)

    def _holder(self, place: int, gate: int) -> int:
        """The one offer holding this seat, and `UNPLACED` where it stands open or two offers hold it between them."""
        at, through = self._at[place], self._through[gate]
        if at != UNPLACED and through != UNPLACED and at != through:
            return UNPLACED

        return at if at != UNPLACED else through

    def _hold(self, offer: int, place: int, gate: int) -> None:
        """Seat the offer at the place and through the gate, all three reading each other afterwards."""
        self._at[place] = offer
        self._through[gate] = offer
        self._taken[offer] = place
        self._gated[offer] = gate

    def _release(self, offer: int, place: int, gate: int) -> None:
        """Let go of the place and the gate an offer left behind on moving to a seat elsewhere."""
        if self._taken[offer] != place:
            self._at[place] = UNPLACED

        if self._gated[offer] != gate:
            self._through[gate] = UNPLACED
