from __future__ import annotations

from pydantic import model_validator

from cardwork.decks.deck import Deck
from cardwork.decks.decks import compare_decks
from cardwork.exceptions import GameValidationError
from cardwork.models.base import BaseFrozen
from cardwork.zones.zone import Zone, ZoneId, Zones


class Board(BaseFrozen):
    """Every card in play, filed under the zone holding it, alongside the deck play started from.

    The board is mechanism: it records where cards sit and who may see them, and leaves to the rules
    what any of that means.
    """

    starting_deck: Deck
    zones: Zones

    @model_validator(mode="after")
    def _keys_match_zone_ids(self) -> Board:
        mismatched = tuple(key for key, zone in self.zones.items() if key != zone.id)
        if mismatched:
            raise ValueError(f"Zones filed under a key other than their own id: {mismatched}")

        return self

    def zone(self, zone_id: ZoneId) -> Zone:
        """The zone under `zone_id`.

        Raises:
            KeyError: when the board holds no zone under that id.
        """
        if zone_id not in self.zones:
            raise KeyError(f"Unknown zone {zone_id!r}; the board holds {sorted(self.zones)}")

        return self.zones[zone_id]

    def with_zones(self, *replacements: Zone) -> Board:
        """Produce a board in which each replacement stands in for the zone sharing its id.

        This is the single mutation point for zone contents, which gives card conservation one place
        to audit and keeps snapshots free of aliasing.
        """
        zones = dict(self.zones)
        zones.update({zone.id: zone for zone in replacements})
        return Board(starting_deck=self.starting_deck, zones=zones)

    def validate_board(self) -> None:
        """Confirm that the cards spread across the zones still add up to the starting deck.

        Raises:
            GameValidationError: when the zones hold a multiset of cards differing from `starting_deck`.
        """
        cards = tuple(card for zone in self.zones.values() for card in zone.cards)
        if len(cards) != len(self.starting_deck):
            raise GameValidationError(
                f"Zones hold {len(cards)} cards while the starting deck holds {len(self.starting_deck)}"
            )

        if not compare_decks(cards, self.starting_deck):
            raise GameValidationError(f"Zones hold {len(cards)} cards differing from the starting deck")
