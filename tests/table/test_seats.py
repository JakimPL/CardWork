from typing import Final

from cardtable.seats import tokens_for

SEATS: Final[int] = 4


def test_every_seat_of_a_table_takes_a_token() -> None:
    assert sorted(tokens_for(SEATS)) == list(range(SEATS))


def test_no_two_seats_share_a_token() -> None:
    tokens = tokens_for(SEATS)

    assert len(set(tokens.values())) == SEATS


def test_a_token_is_drawn_rather_than_read_off_the_seat_it_holds() -> None:
    assert tokens_for(SEATS) != tokens_for(SEATS)
