from typing import Final

from cardwork.decks.deck import Deck
from cardwork.decks.decks import to_game_cards
from cardwork.zones import presets
from cardwork.zones.family import Family
from cardwork.zones.zone import Zone, ZoneId, Zones
from cardwork.zones.zones import HANDS, discard

STOCK: Final[ZoneId] = "stock"
SEALED_CARD: Final[int] = 0

BLINDS: Final[Family] = Family(
    name="blind",
    ordered=True,
    visibility=presets.HIDDEN,
)
TRAYS: Final[Family] = Family(
    name="tray",
    ordered=True,
    visibility=presets.HIDDEN,
)
HOLDINGS: Final[tuple[Family, ...]] = (HANDS, BLINDS)


def showdown_zones(players: int, deck: Deck) -> Zones:
    """The table a showdown round is played on: two holdings and a tray for each seat, the stock and the discard.

    A hand is the five cards a seat reads and a blind the five it does not, which are the two holdings a
    commitment comes out of. Each is a family standing at every seat, so the name of the family is the word a
    commitment names its holding by and the seat says which zone that word reaches.

    A hand lies face down, which its owner reads and the rest of the table reads the size of. A blind and a tray
    lie under the policy reading to nobody, so the five a seat may not read stay unread by everybody its owner
    included, and a commitment stays sealed until it turns. The stock and the discard share the pile policy,
    which reads a card the moment it lies face up: what is still to be dealt stays unknown, and every card
    revealed is read by the whole table.

    A hand is the one holding its seat arranges. The run of a blind is the order the deal laid it in, which the
    turns read a card out of by position, and the run of a tray is the order the commitments were made in, so
    the table keeps both.
    """
    return {
        **HANDS.zones(players),
        **BLINDS.zones(players),
        **TRAYS.zones(players),
        STOCK: Zone(
            id=STOCK,
            visibility=presets.PILE,
            ordered=True,
            cards=to_game_cards(deck, face_down=True),
        ),
        **discard(),
    }
