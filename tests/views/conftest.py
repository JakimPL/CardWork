from typing import Final

import pytest

from cardwork.boards.board import Board
from cardwork.cards.cards import (
    ACE_OF_SPADES,
    FIVE_OF_SPADES,
    FOUR_OF_SPADES,
    JACK_OF_DIAMONDS,
    KING_OF_HEARTS,
    QUEEN_OF_CLUBS,
    SEVEN_OF_SPADES,
    SIX_OF_SPADES,
    THREE_OF_SPADES,
    TWO_OF_SPADES,
)
from cardwork.cards.game import GameCard
from cardwork.decks.deck import Deck
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.zones.presets import HAND, HIDDEN, PILE
from cardwork.zones.zone import Zone, Zones

PLAYERS: Final[int] = 3
SEQ: Final[int] = 7

HELD_BY_ZERO: Final[GameCard] = GameCard(card=ACE_OF_SPADES, face_down=True)
ALSO_HELD_BY_ZERO: Final[GameCard] = GameCard(card=KING_OF_HEARTS, face_down=True)
EXPOSED_BY_ZERO: Final[GameCard] = GameCard(card=TWO_OF_SPADES, face_down=False)
HELD_BY_ONE: Final[GameCard] = GameCard(card=QUEEN_OF_CLUBS, face_down=True)
ALSO_HELD_BY_ONE: Final[GameCard] = GameCard(card=JACK_OF_DIAMONDS, face_down=True)
BLIND_OF_ZERO: Final[GameCard] = GameCard(card=THREE_OF_SPADES, face_down=True)
DISCARDED: Final[GameCard] = GameCard(card=FOUR_OF_SPADES, face_down=False)
UNDRAWN: Final[GameCard] = GameCard(card=FIVE_OF_SPADES, face_down=True)
ALSO_UNDRAWN: Final[GameCard] = GameCard(card=SIX_OF_SPADES, face_down=True)
VAULTED: Final[GameCard] = GameCard(card=SEVEN_OF_SPADES, face_down=False)

LAYOUT: Final[Zones] = {
    "hand:0": Zone(id="hand:0", owner=0, visibility=HAND, cards=(HELD_BY_ZERO, ALSO_HELD_BY_ZERO, EXPOSED_BY_ZERO)),
    "hand:1": Zone(id="hand:1", owner=1, visibility=HAND, cards=(HELD_BY_ONE, ALSO_HELD_BY_ONE)),
    "blind:0": Zone(id="blind:0", owner=0, visibility=PILE, cards=(BLIND_OF_ZERO,)),
    "discard": Zone(id="discard", visibility=PILE, cards=(DISCARDED,)),
    "draw": Zone(id="draw", visibility=PILE, cards=(UNDRAWN, ALSO_UNDRAWN)),
    "vault": Zone(id="vault", visibility=HIDDEN, cards=(VAULTED,)),
}

DECK: Final[Deck] = tuple(game_card.card for zone in LAYOUT.values() for game_card in zone.cards)


@pytest.fixture(name="board")
def board_fixture() -> Board:
    return Board(starting_deck=DECK, zones=LAYOUT)


@pytest.fixture(name="position")
def position_fixture(board: Board) -> Position[GameState]:
    return Position(board=board, state=GameState(phase="play", to_act=frozenset({1})), players=PLAYERS)
