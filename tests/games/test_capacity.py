from dataclasses import dataclass
from random import Random
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.exceptions import GameValidationError
from cardwork.games.capacity import Capacity
from cardwork.games.game import Game
from tests.cases import Case, descriptions

from .conftest import SEED
from .demo import DECK, SEATS, DiscardGame

NO_SEATS: Final[int] = 0
ONE_SEAT: Final[int] = 1
TWO_SEATS: Final[int] = 2
MIDDLING: Final[int] = 4
FULL_TABLE: Final[int] = 5
CROWDED: Final[int] = 6
A_SMALL_TABLE: Final[Capacity] = Capacity(least=TWO_SEATS, most=FULL_TABLE)
ONE_SIZE_ONLY: Final[Capacity] = Capacity(least=FULL_TABLE, most=FULL_TABLE)


@dataclass(frozen=True)
class SeatingCase(Case):
    """One table size beside whether each of the two capacities is played at a table that size."""

    players: int
    small: bool
    fixed: bool


SEATINGS: Final[tuple[SeatingCase, ...]] = (
    SeatingCase(description="a table of no seats at all", players=NO_SEATS, small=False, fixed=False),
    SeatingCase(description="a table one seat short of the fewest", players=ONE_SEAT, small=False, fixed=False),
    SeatingCase(description="a table of the fewest seats", players=TWO_SEATS, small=True, fixed=False),
    SeatingCase(description="a table between the two ends", players=MIDDLING, small=True, fixed=False),
    SeatingCase(description="a table of the most seats", players=FULL_TABLE, small=True, fixed=True),
    SeatingCase(description="a table one seat past the most", players=CROWDED, small=False, fixed=False),
)


@pytest.mark.parametrize("case", SEATINGS, ids=descriptions(SEATINGS))
def test_a_capacity_admits_the_tables_its_game_is_played_at(case: SeatingCase) -> None:
    assert A_SMALL_TABLE.admits(case.players) is case.small
    assert ONE_SIZE_ONLY.admits(case.players) is case.fixed


def test_a_capacity_lets_every_table_it_admits_stand() -> None:
    for players in range(A_SMALL_TABLE.least, A_SMALL_TABLE.most + 1):
        A_SMALL_TABLE.confirm(players)


def test_a_table_of_another_size_is_refused_naming_the_seating_the_game_is_played_at() -> None:
    with pytest.raises(GameValidationError, match=f"seats {TWO_SEATS} to {FULL_TABLE} players, and {CROWDED}"):
        A_SMALL_TABLE.confirm(CROWDED)


def test_a_game_played_at_one_size_states_that_size_alone_in_its_refusal() -> None:
    with pytest.raises(GameValidationError, match=f"seats {FULL_TABLE} players, and {TWO_SEATS}"):
        ONE_SIZE_ONLY.confirm(TWO_SEATS)


def test_a_game_is_played_at_a_table_of_one_seat_at_the_least() -> None:
    with pytest.raises(ValidationError):
        Capacity(least=NO_SEATS, most=FULL_TABLE)


def test_a_game_needing_more_seats_than_it_holds_is_refused() -> None:
    with pytest.raises(ValidationError, match="holds that many or more"):
        Capacity(least=FULL_TABLE, most=TWO_SEATS)


def test_the_engine_holds_a_table_to_the_seating_its_game_declares() -> None:
    assert DiscardGame.capacity.admits(SEATS)

    with pytest.raises(GameValidationError, match=f"seats {TWO_SEATS} to {FULL_TABLE} players"):
        DiscardGame(players=ONE_SEAT, deck=DECK, rng=Random(SEED))


def test_the_engine_states_no_seating_of_its_own_for_a_game_to_fall_back_on() -> None:
    assert "capacity" not in vars(Game)
