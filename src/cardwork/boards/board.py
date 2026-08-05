from __future__ import annotations

from pydantic import model_validator

from cardwork.cards.game import CardsOrJokers
from cardwork.decks.deck import Deck, Indices
from cardwork.decks.decks import compare_decks, named
from cardwork.exceptions import GameValidationError, LogicError
from cardwork.models.base import BaseFrozen
from cardwork.zones.zone import Zone, ZoneId, Zones, cards_of


class Board(BaseFrozen):
    """Every card in play, filed under the zone holding it, alongside the deck play started from.

    The board is mechanism: it records where cards sit and who may see them, and leaves to the rules
    what any of that means.

    Every reading the board answers is addressed by the id of one zone, since a zone is as much as the
    board knows: how many cards lie there, which cards they are, what stands at the end of the run, and
    what the places of a move name. A reading refuses an id the board holds no zone under, which names a
    missing zone at the reading that wants it.
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

    def cards(self, zone_id: ZoneId) -> CardsOrJokers:
        """The cards one zone holds as the rules read them, apart from the face they lie at."""
        return cards_of(self.zone(zone_id))

    def count(self, zone_id: ZoneId) -> int:
        """How many cards one zone holds, which is what a rule reading a hand by its length asks."""
        return len(self.zone(zone_id).cards)

    def holds(self, zone_id: ZoneId) -> bool:
        """Whether one zone holds a card, which is what a stock still worth drawing from answers to."""
        return bool(self.zone(zone_id).cards)

    def top(self, zone_id: ZoneId, count: int) -> CardsOrJokers:
        """The last cards of a run, which is the end a pile is read from.

        A pile is read from its top: the cards laid on last stand at the end of the run, so a play that put
        three cards there is read by taking three off the top. Reading none of them gives no cards.

        Args:
            zone_id: the zone whose run is read.
            count: how many cards are read off the top, up to the whole of the run.

        Raises:
            LogicError: when the count is negative, or names more cards than the zone holds.
        """
        held = self.count(zone_id)
        if not 0 <= count <= held:
            raise LogicError(f"Zone {zone_id!r} holds {held} cards, and {count} were read off its top")

        return self.cards(zone_id)[held - count :]

    def taken(self, zone_id: ZoneId, indices: Indices) -> CardsOrJokers:
        """The cards the given places name, out of the run one zone holds, in the run's own order.

        Raises:
            KeyError: when a place lies past the cards the zone holds.
        """
        return named(self.cards(zone_id), indices)

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
