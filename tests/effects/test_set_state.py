from cardwork.boards.board import Board
from cardwork.effects.effects import SetState
from cardwork.positions.position import Position
from cardwork.states.state import GameState


class BiddingState(GameState):
    trump: str
    highest_bid: int | None = None


def a_bidding_position(board: Board) -> Position[BiddingState]:
    return Position(board=board, state=BiddingState(phase="bid", to_act=frozenset({0}), trump="♠"), players=2)


def test_set_state_swaps_the_rules_cursor(position: Position[GameState]) -> None:
    effect: SetState[GameState] = SetState(state=GameState(phase="score", to_act=frozenset()))

    settled = effect.apply(position)

    assert settled.state == GameState(phase="score", to_act=frozenset())


def test_set_state_leaves_the_board_as_it_lies(position: Position[GameState]) -> None:
    effect: SetState[GameState] = SetState(state=GameState(phase="score"))

    assert effect.apply(position).board == position.board


def test_set_state_carries_a_game_s_own_state_fields(board: Board) -> None:
    position = a_bidding_position(board)
    effect = SetState[BiddingState](state=position.state.with_changes(highest_bid=3))

    bid = effect.apply(position)

    assert bid.state.trump == "♠"
    assert bid.state.highest_bid == 3


def test_set_state_round_trips_a_game_s_own_state_fields() -> None:
    effect = SetState[BiddingState](state=BiddingState(phase="bid", trump="♥", highest_bid=2))

    restored = SetState[BiddingState].model_validate_json(effect.model_dump_json())

    assert restored == effect


def test_set_state_carries_a_state_of_the_game_s_own_type(board: Board) -> None:
    position = a_bidding_position(board)
    effect = SetState[BiddingState](state=position.state.with_changes(phase="play"))

    assert isinstance(effect.apply(position).state, BiddingState)
