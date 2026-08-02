from __future__ import annotations

from collections.abc import Mapping

from cardwork.decks.deck import GameCards
from cardwork.models.base import BaseFrozen
from cardwork.zones.visibility import Visibility

ZoneId = str


class Zone(BaseFrozen):
    """A named, ordered collection of cards with an owner and a visibility policy.

    A hand, a draw pile, a discard stack and a played meld are all this one shape; the visibility
    policy and the presence of an owning seat are what tell them apart.
    """

    id: ZoneId
    owner: int | None = None
    visibility: Visibility
    cards: GameCards = ()

    def with_cards(self, cards: GameCards) -> Zone:
        """The same zone holding the given cards, under its own id, owner and visibility policy."""
        return Zone(
            id=self.id,
            owner=self.owner,
            visibility=self.visibility,
            cards=cards,
        )


Zones = Mapping[ZoneId, Zone]
