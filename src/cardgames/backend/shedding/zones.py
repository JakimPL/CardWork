from typing import Final

from cardwork.decks.deck import Deck
from cardwork.decks.decks import to_game_cards
from cardwork.zones import presets
from cardwork.zones.zone import Zone, ZoneId, Zones
from cardwork.zones.zones import HANDS, discard

STOCK: Final[ZoneId] = "stock"


def shedding_zones(players: int, deck: Deck) -> Zones:
    """The table a shedding round is played on: a hand for each seat, the stock it draws from, the discard it sheds onto.

    A hand is the family standing at every seat, so `HANDS.name` is the word a shed names its group by and the
    seat says which zone that word reaches. It lies face down, which its owner reads and the rest of the table
    reads the size of. The stock lies face down under the pile policy and the discard face up under the same
    one, so what a seat sheds is read by everybody while what it stands to draw stays unknown to all.

    The stock is dealt from one end of its run and drawn from the other, which a shuffled pile of backs is
    indifferent to: `rules.drawn_from` states which end a turn takes, and it is the end a player points at.
    """
    return {
        **HANDS.zones(players),
        STOCK: Zone(
            id=STOCK,
            visibility=presets.PILE,
            ordered=True,
            cards=to_game_cards(deck, face_down=True),
        ),
        **discard(),
    }
