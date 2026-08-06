from __future__ import annotations

from collections.abc import Mapping

from cardwork.cards.game import CardsOrJokers
from cardwork.decks.deck import GameCards
from cardwork.models.base import BaseFrozen
from cardwork.zones.visibility import Visibility

ZoneId = str


class Zone(BaseFrozen):
    """A named run of cards with an owner, a visibility policy, and a word on what its arrangement holds.

    A hand, a draw pile, a discard stack and a played meld are all this one shape; the visibility
    policy, the presence of an owning seat and whether the run itself carries meaning are what tell
    them apart.

    `ordered` says whether the run the cards lie in is part of what the zone holds. A pile dealt from and a
    stack laid onto are ordered: the card that comes off next and the card lying on top are named by
    position, so the run is the record of the round. A hand holds the cards a seat has under an arrangement
    of the seat's own, which is what leaves an unordered zone one its owner may lay out as it pleases.

    The word binds the players alone. The rules reorder whatever they need to — a shuffle of the stock is a
    `Reorder` over an ordered pile — and `ordered` settles which zones a seat may arrange for its own sake.
    """

    id: ZoneId
    owner: int | None = None
    visibility: Visibility
    ordered: bool
    cards: GameCards = ()

    def with_cards(self, cards: GameCards) -> Zone:
        """The same zone holding the given cards, under its own id, owner, visibility policy and arrangement."""
        return Zone(
            id=self.id,
            owner=self.owner,
            visibility=self.visibility,
            ordered=self.ordered,
            cards=cards,
        )


def cards_of(zone: Zone) -> CardsOrJokers:
    """The cards a zone holds as the rules read them, apart from the face they lie at.

    Faces decide who sees a card, which is the projection's affair; the rules read the cards themselves.
    """
    return tuple(game_card.card for game_card in zone.cards)


Zones = Mapping[ZoneId, Zone]
