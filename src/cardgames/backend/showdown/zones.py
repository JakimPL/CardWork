from enum import StrEnum
from typing import Final

from cardwork.decks.deck import Deck
from cardwork.decks.decks import to_game_cards
from cardwork.zones import presets
from cardwork.zones.zone import Zone, ZoneId, Zones

STOCK: Final[ZoneId] = "stock"
DISCARD: Final[ZoneId] = "discard"
TRAY: Final[str] = "tray"
SEALED_CARD: Final[int] = 0


class Holding(StrEnum):
    """The two holdings a seat commits from, which is the word a commitment names beside its card.

    A hand is the five cards a seat reads; a blind is the five it does not. Both are the seat's own, so the
    word and the seat together name the zone the card comes out of.
    """

    HAND = "hand"
    BLIND = "blind"


HOLDINGS: Final[tuple[Holding, ...]] = tuple(Holding)


def zone_of(holding: Holding, seat: int) -> ZoneId:
    """The zone one seat's holding stands for, which is what the word a commitment names resolves to."""
    return f"{holding}:{seat}"


def hand_of(seat: int) -> ZoneId:
    return zone_of(Holding.HAND, seat)


def blind_of(seat: int) -> ZoneId:
    return zone_of(Holding.BLIND, seat)


def tray_of(seat: int) -> ZoneId:
    return f"{TRAY}:{seat}"


def showdown_zones(players: int, deck: Deck) -> Zones:
    """The table a showdown round is played on: two holdings and a tray for each seat, the stock and the discard.

    A hand lies face down, which its owner reads and the rest of the table reads the size of. A blind and a tray
    lie under the policy reading to nobody, so the five a seat may not read stay unread by everybody its owner
    included, and a commitment stays sealed until it turns. The stock and the discard share the pile policy,
    which reads a card the moment it lies face up: what is still to be dealt stays unknown, and every card
    revealed is read by the whole table.
    """
    seated = {
        zone.id: zone
        for seat in range(players)
        for zone in (
            Zone(id=hand_of(seat), owner=seat, visibility=presets.HAND),
            Zone(id=blind_of(seat), owner=seat, visibility=presets.HIDDEN),
            Zone(id=tray_of(seat), owner=seat, visibility=presets.HIDDEN),
        )
    }
    return {
        **seated,
        STOCK: Zone(
            id=STOCK,
            visibility=presets.PILE,
            cards=to_game_cards(deck, face_down=True),
        ),
        DISCARD: Zone(id=DISCARD, visibility=presets.PILE),
    }
