from collections.abc import Sequence
from typing import Final

UNPLACED: Final[int] = -1


class Matching:
    """Offers and the places they answer, each offer given a place of its own.

    `admitted[offer]` lists the places that offer answers, and `placements` states the place each offer took.
    Two properties carry the search that reads a hand into a combination: as many places are filled as any
    assignment could fill, and among the assignments filling that many, the offers standing earliest are the
    ones placed — so reading a hand from its strongest card downwards fills a combination with the strongest
    cards it can hold.
    """

    def __init__(self, admitted: Sequence[Sequence[int]], places: int) -> None:
        self._admitted = admitted
        self._holder: list[int] = [UNPLACED] * places
        self._taken: list[int] = [UNPLACED] * len(admitted)
        for offer in range(len(admitted)):
            self._place(offer, set())

    @property
    def placements(self) -> tuple[int, ...]:
        """The place each offer took, holding `UNPLACED` for an offer that answers held places alone."""
        return tuple(self._taken)

    def _place(self, offer: int, tried: set[int]) -> bool:
        """Find this offer a place and say whether one was found.

        A place standing open goes to the offer directly. Where every place it answers is held, the offer asks
        each holder in turn to move on and takes the place of the first holder that finds another, so that one
        chain of moves reaches every place such a rearrangement opens.
        """
        for place in self._admitted[offer]:
            if self._holder[place] == UNPLACED:
                self._hold(place, offer)
                return True

        for place in self._admitted[offer]:
            if place in tried:
                continue

            tried.add(place)
            if self._place(self._holder[place], tried):
                self._hold(place, offer)
                return True

        return False

    def _hold(self, place: int, offer: int) -> None:
        """Give the place to the offer, both of them reading each other afterwards."""
        self._holder[place] = offer
        self._taken[offer] = place
