import pytest

from cardwork.exceptions import CardworkError, IllegalMove, NotYourTurn, StalePosition, UndoUnavailable

HIERARCHY = (IllegalMove, NotYourTurn, StalePosition, UndoUnavailable)


@pytest.mark.parametrize("error_type", HIERARCHY, ids=lambda error_type: error_type.__name__)
def test_every_domain_error_is_catchable_as_a_cardwork_error(error_type: type[CardworkError]) -> None:
    assert issubclass(error_type, CardworkError)
    assert issubclass(error_type, Exception)


def test_not_your_turn_records_the_seats_that_owe_an_action() -> None:
    error = NotYourTurn(player=3, to_act=frozenset({0, 1}))

    assert error.player == 3
    assert error.to_act == frozenset({0, 1})
    assert "3" in str(error)


def test_stale_position_records_both_sequence_numbers() -> None:
    error = StalePosition(base_seq=4, head=7)

    assert error.base_seq == 4
    assert error.head == 7


def test_illegal_move_records_the_reason() -> None:
    error = IllegalMove(reason="a spade was led")

    assert error.reason == "a spade was led"
    assert str(error) == "a spade was led"
