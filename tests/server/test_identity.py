import pytest

from cardserver.errors import Unauthenticated, WrongSeat
from cardserver.identity import TokenSeats, confirm_actor

from .conftest import TABLE, UNSERVED, token_of

SEATS_HELD = TokenSeats({TABLE: {token_of(0): 0, token_of(1): 1}})


def test_a_token_names_the_seat_it_was_issued_for() -> None:
    assert SEATS_HELD.seat(TABLE, token_of(1)) == 1


def test_a_client_offering_no_token_watches() -> None:
    assert SEATS_HELD.seat(TABLE, None) is None


def test_a_token_the_table_never_issued_is_turned_away() -> None:
    with pytest.raises(Unauthenticated):
        SEATS_HELD.seat(TABLE, "picked-up-somewhere")


def test_a_token_issued_elsewhere_is_turned_away() -> None:
    with pytest.raises(Unauthenticated):
        SEATS_HELD.seat(UNSERVED, token_of(0))


def test_a_seat_acts_for_itself() -> None:
    assert confirm_actor(0, 0) is None


def test_a_seat_acts_for_no_other() -> None:
    with pytest.raises(WrongSeat):
        confirm_actor(0, 1)


def test_a_spectator_acts_at_no_seat() -> None:
    with pytest.raises(WrongSeat):
        confirm_actor(None, 0)
