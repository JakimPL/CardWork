from cardwork.cards.card import Card, Facing
from cardwork.combinations.spread import Spread


class Gates:
    """The gates the cards of one run reach a shape's places through, a gate seating one card at a time.

    A place reading apart in no spread stands behind a gate of its own, so what that place asks is the whole of
    what a card answers there. The places of a spread stand behind a gate for each facing the spread reads, which
    is what holds two cards facing alike to one place of that spread between them.

    A gate is named as it is first reached, so `len` states how many the run came to.
    """

    def __init__(self, places: int) -> None:
        self._places = places
        self._kept: dict[tuple[Spread, Facing], int] = {}

    def of(self, place: int, spread: Spread | None, card: Card) -> int:
        """The gate this card reaches that place through, which every card facing as it does reaches too."""
        if spread is None:
            return place

        return self._kept.setdefault((spread, spread.read(card)), self._places + len(self._kept))

    def __len__(self) -> int:
        """How many gates the places and the facings reached come to between them."""
        return self._places + len(self._kept)
