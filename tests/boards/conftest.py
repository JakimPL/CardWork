from typing import Final

import pytest

from cardwork.boards.board import Board
from cardwork.cards.cards import ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS
from cardwork.decks.deck import Deck
from cardwork.decks.decks import to_game_cards
from cardwork.zones.presets import HAND, PILE
from cardwork.zones.zone import Zone

DECK: Final[Deck] = (ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS)


@pytest.fixture(name="hand")
def hand_fixture() -> Zone:
    return Zone(
        id="hand:0",
        owner=0,
        visibility=HAND,
        cards=to_game_cards((ACE_OF_SPADES, KING_OF_HEARTS), face_down=True),
    )


@pytest.fixture(name="draw")
def draw_fixture() -> Zone:
    return Zone(id="draw", visibility=PILE, cards=to_game_cards((QUEEN_OF_CLUBS,), face_down=True))


@pytest.fixture(name="board")
def board_fixture(hand: Zone, draw: Zone) -> Board:
    return Board(starting_deck=DECK, zones={hand.id: hand, draw.id: draw})
