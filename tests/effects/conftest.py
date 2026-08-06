from typing import Final

import pytest

from cardwork.boards.board import Board
from cardwork.cards.cards import (
    ACE_OF_SPADES,
    KING_OF_HEARTS,
    QUEEN_OF_CLUBS,
    TWO_OF_SPADES,
)
from cardwork.decks.deck import Deck
from cardwork.decks.decks import to_game_cards
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.zones.presets import PILE
from cardwork.zones.zone import Zone

HAND_CARDS: Final[Deck] = (ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS)
TABLE_CARDS: Final[Deck] = (TWO_OF_SPADES,)
DECK: Final[Deck] = HAND_CARDS + TABLE_CARDS
PLAYERS: Final[int] = 2


@pytest.fixture(name="board")
def board_fixture() -> Board:
    zones = (
        Zone(id="hand:0", owner=0, visibility=PILE, ordered=False, cards=to_game_cards(HAND_CARDS, face_down=True)),
        Zone(id="table", visibility=PILE, ordered=True, cards=to_game_cards(TABLE_CARDS, face_down=False)),
        Zone(
            id="discard",
            visibility=PILE,
            ordered=True,
        ),
    )
    return Board(starting_deck=DECK, zones={zone.id: zone for zone in zones})


@pytest.fixture(name="position")
def position_fixture(board: Board) -> Position[GameState]:
    return Position(board=board, state=GameState(phase="play", to_act=frozenset({0})), players=PLAYERS)
