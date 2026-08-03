from typing import Final

from cardwork.cards.game import CardsOrJokers
from cardwork.decks.deck import Deck
from cardwork.decks.decks import to_game_cards
from cardwork.zones import presets
from cardwork.zones.zone import Zone, ZoneId, Zones

PILE: Final[ZoneId] = "pile"
STACK: Final[ZoneId] = "stack"
TOP_OF_THE_PILE: Final[int] = 0


def hand_of(seat: int) -> ZoneId:
    return f"hand:{seat}"


def passing_zones(players: int, deck: Deck) -> Zones:
    """The table a passing round is played on: a hand for each seat, the pile it draws from, the stack it lays on.

    A hand lies face down, which its owner reads and the rest of the table reads the size of. The pile lies
    face down under one policy and the stack face up under the same one, so what a seat gives up is read by
    everybody while what it may take stays unknown to all.
    """
    hands = {hand_of(seat): Zone(id=hand_of(seat), owner=seat, visibility=presets.HAND) for seat in range(players)}
    return {
        **hands,
        PILE: Zone(id=PILE, visibility=presets.PILE, cards=to_game_cards(deck, face_down=True)),
        STACK: Zone(id=STACK, visibility=presets.PILE),
    }


def cards_of(zone: Zone) -> CardsOrJokers:
    """The cards a zone holds as the rules read them, apart from the face they lie at."""
    return tuple(game_card.card for game_card in zone.cards)
