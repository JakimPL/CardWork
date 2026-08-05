from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.exceptions import LogicError
from cardwork.rounds.seating import followed, following, next_seat, rotation
from tests.cases import Case, descriptions

SEATS: Final[int] = 4
LAST_SEAT: Final[int] = 3
STILL_IN: Final[frozenset[int]] = frozenset({1, 3})
EVERY_SEAT: Final[frozenset[int]] = frozenset(range(SEATS))
NOBODY: Final[frozenset[int]] = frozenset()


def among(seats: frozenset[int]) -> Callable[[int], bool]:
    """Whether a seat stands among those, which is the shape a search round the table is given."""
    return seats.__contains__


def test_the_seat_next_round_the_table_wraps_at_the_last() -> None:
    assert next_seat(LAST_SEAT, SEATS) == 0


def test_a_rotation_reads_every_seat_from_the_leader_onwards() -> None:
    assert rotation(2, SEATS) == (2, 3, 0, 1)


@dataclass(frozen=True)
class SearchCase(Case):
    """One search round the table beside the seat it reaches, or None where no seat of the table answers."""

    seat: int
    admitted: frozenset[int]
    including: bool
    found: int | None


SEARCHES: Final[tuple[SearchCase, ...]] = (
    SearchCase(
        description="the next seat admitted is the one the turn travels to",
        seat=0,
        admitted=STILL_IN,
        including=False,
        found=1,
    ),
    SearchCase(
        description="a search past the last seat wraps round to the first",
        seat=LAST_SEAT,
        admitted=STILL_IN,
        including=False,
        found=1,
    ),
    SearchCase(
        description="a seat set out from is passed over where it answers for nobody",
        seat=1,
        admitted=STILL_IN,
        including=False,
        found=LAST_SEAT,
    ),
    SearchCase(
        description="a seat that answers for itself keeps the turn where it stands",
        seat=1,
        admitted=STILL_IN,
        including=True,
        found=1,
    ),
    SearchCase(
        description="a seat answering for itself is passed over where it is not admitted",
        seat=0,
        admitted=STILL_IN,
        including=True,
        found=1,
    ),
    SearchCase(
        description="a search of a table admitting every seat reaches the next one",
        seat=2,
        admitted=EVERY_SEAT,
        including=False,
        found=LAST_SEAT,
    ),
    SearchCase(
        description="a table admitting no seat at all is reached round in full and answered with none",
        seat=0,
        admitted=NOBODY,
        including=False,
        found=None,
    ),
    SearchCase(
        description="the one seat admitted is found by the search that sets out from it",
        seat=2,
        admitted=frozenset({2}),
        including=False,
        found=2,
    ),
)


@pytest.mark.parametrize("case", SEARCHES, ids=descriptions(SEARCHES))
def test_a_search_round_the_table_reaches_the_first_seat_it_admits(case: SearchCase) -> None:
    assert following(case.seat, SEATS, among(case.admitted), including=case.including) == case.found


def test_a_search_held_to_a_seat_answers_with_the_one_it_reaches() -> None:
    assert followed(0, SEATS, among(STILL_IN), including=False) == 1


def test_a_search_held_to_a_seat_refuses_a_table_no_seat_of_which_answers() -> None:
    with pytest.raises(LogicError, match=f"No seat of the {SEATS} at this table follows seat 0"):
        followed(0, SEATS, among(NOBODY), including=False)
