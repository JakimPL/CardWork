from typing import Final

from cardwork.boards.board import Board
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.transactions.journal import Journal
from cardwork.transactions.transaction import Transaction

PLAYERS: Final[int] = 4


class TrickState(GameState):
    trump: str
    led_by: int | None = None


def a_position() -> Position[TrickState]:
    return Position(
        board=Board(starting_deck=(), zones={}),
        state=TrickState(phase="play", to_act=frozenset({1}), trump="♠", led_by=0),
        players=PLAYERS,
    )


def test_a_game_keeps_its_own_state_fields_through_a_position_round_trip() -> None:
    position = a_position()

    restored = Position[TrickState].model_validate_json(position.model_dump_json())

    assert restored == position
    assert restored.state.trump == "♠"
    assert restored.state.led_by == 0


def test_with_state_returns_the_game_s_own_state_type() -> None:
    position = a_position()

    advanced = position.with_state(position.state.model_copy(update={"led_by": 2}))

    assert advanced.state.trump == "♠"
    assert advanced.state.led_by == 2


def test_a_journal_of_a_game_s_own_state_replays_to_its_origin() -> None:
    position = a_position()
    journal: Journal[TrickState] = Journal(initial=position)

    extended = journal.append(Transaction(seq=0, move=None, effects=()))

    assert extended.head == 1
    assert extended.replay() == position
