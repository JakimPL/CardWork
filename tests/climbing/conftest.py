import pytest

from cardgames.backend.climbing.game import ClimbingGame
from cardwork.rounds.conclusion import ONE_ROUND

from .driving import FOUR_SEATS, ROUNDS, SEATS, SEED, TWO_SEATS, a_match


@pytest.fixture(name="climbing")
def climbing_fixture() -> ClimbingGame:
    return a_match(SEATS, ROUNDS, SEED)


@pytest.fixture(name="four_seats")
def four_seats_fixture() -> ClimbingGame:
    return a_match(FOUR_SEATS, ROUNDS, SEED)


@pytest.fixture(name="two_seats")
def two_seats_fixture() -> ClimbingGame:
    return a_match(TWO_SEATS, ONE_ROUND, SEED)
