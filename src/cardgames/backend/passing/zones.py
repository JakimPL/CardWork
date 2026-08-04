from typing import Final

from cardwork.decks.deck import Deck
from cardwork.decks.decks import to_game_cards
from cardwork.zones import presets
from cardwork.zones.zone import Zone, ZoneId, Zones
from cardwork.zones.zones import hands, stack

PILE: Final[ZoneId] = "pile"
TOP_OF_THE_PILE: Final[int] = 0


def passing_zones(players: int, deck: Deck) -> Zones:
    """The table a passing round is played on: a hand for each seat, the pile it draws from, the stack it lays on.

    A hand lies face down, which its owner reads and the rest of the table reads the size of. The pile lies
    face down under one policy and the stack face up under the same one, so what a seat gives up is read by
    everybody while what it may take stays unknown to all.
    """
    return {
        **hands(players),
        PILE: Zone(
            id=PILE,
            visibility=presets.PILE,
            ordered=True,
            cards=to_game_cards(
                deck,
                face_down=True,
            ),
        ),
        **stack(),
    }
