import pytest

from cardwork.rounds.state import BEFORE_THE_FIRST_ROUND, RoundState

FRESH = "fresh"


def test_a_cursor_stands_before_the_first_round_until_one_opens() -> None:
    state = RoundState(phase=FRESH)

    assert state.round_number == BEFORE_THE_FIRST_ROUND
    assert state.leader is None
    assert state.round_points == ()
    assert state.points is None


def test_a_cursor_before_the_first_round_names_no_leading_seat() -> None:
    state = RoundState(phase=FRESH)

    with pytest.raises(ValueError, match="No round has opened"):
        state.led_by  # pylint: disable=pointless-statement


def test_a_cursor_of_an_open_round_names_the_seat_leading_it() -> None:
    state = RoundState(phase=FRESH, round_number=3, leader=2, round_points=(0, 4))

    assert state.led_by == 2
    assert state.round_number == 3
