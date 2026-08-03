import pytest

from cardgames.backend.showdown.game import ONE_ROUND, ShowdownGame

from .driving import ROUNDS, SEATS, SEED, TWO_SEATS, a_match


@pytest.fixture(name="showdown")
def showdown_fixture() -> ShowdownGame:
    return a_match(SEATS, ROUNDS, SEED)


@pytest.fixture(name="two_seats")
def two_seats_fixture() -> ShowdownGame:
    return a_match(TWO_SEATS, ONE_ROUND, SEED)
