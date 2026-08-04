from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.boards.board import Board
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.zones.presets import PILE
from cardwork.zones.zone import Zone

PLAYERS: Final[int] = 2


@pytest.fixture(name="position")
def position_fixture() -> Position[GameState]:
    board = Board(starting_deck=(), zones={})
    return Position(board=board, state=GameState(phase="deal", to_act=frozenset({0})), players=PLAYERS)


def test_with_board_carries_the_state_and_the_seat_count(position: Position[GameState]) -> None:
    extended = position.with_board(
        position.board.with_zones(
            Zone(
                id="draw",
                visibility=PILE,
                ordered=True,
            )
        )
    )

    assert extended.state == position.state
    assert extended.players == PLAYERS
    assert "draw" in extended.board.zones


def test_with_state_carries_the_board_and_the_seat_count(position: Position[GameState]) -> None:
    advanced = position.with_state(GameState(phase="play", to_act=frozenset({1})))

    assert advanced.board == position.board
    assert advanced.players == PLAYERS
    assert advanced.state.phase == "play"


def test_with_state_leaves_the_position_it_was_called_on_intact(position: Position[GameState]) -> None:
    position.with_state(GameState(phase="play"))

    assert position.state.phase == "deal"


def test_position_requires_at_least_one_seat() -> None:
    with pytest.raises(ValidationError):
        Position(board=Board(starting_deck=(), zones={}), state=GameState(phase="deal"), players=0)
