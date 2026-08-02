import pytest

from cardwork.states.state import GameState


def test_current_names_the_single_seat_owing_an_action() -> None:
    assert GameState(phase="play", to_act=frozenset({2})).current == 2


def test_current_stays_open_while_several_seats_owe_an_action() -> None:
    assert GameState(phase="arrange", to_act=frozenset({0, 1, 2})).current is None


def test_current_stays_open_once_the_round_has_closed() -> None:
    assert GameState(phase="reveal").current is None


def test_state_rejects_attribute_assignment() -> None:
    state = GameState(phase="play")

    with pytest.raises(ValueError):
        state.phase = "reveal"


def test_points_are_stored_as_an_immutable_run() -> None:
    state = GameState(phase="score", points=[3, 5])

    assert state.points == (3, 5)
