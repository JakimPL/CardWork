from collections.abc import Mapping

from cardwork.decks.deck import Deck
from cardwork.decks.decks import compare_decks
from cardwork.models.base import BaseFrozen
from cardwork.zones.zone import Zone


class Board(BaseFrozen):
    starting_deck: Deck
    zones: Mapping[str, Zone]

    def validate_board(self) -> None:
        cards = tuple(card for zone in self.zones.values() for card in zone.cards)
        if compare_decks(cards, self.starting_deck):
            raise ValueError("Cards don't match")
