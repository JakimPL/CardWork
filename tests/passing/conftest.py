import pytest

from cardgames.passing.game import PassingGame

from .driving import JOKERED_DECK, PLAIN_DECK, SEATS, SEED, TWO_SEATS, a_match


@pytest.fixture(name="passing")
def passing_fixture() -> PassingGame:
    return a_match(SEATS, JOKERED_DECK, SEED)


@pytest.fixture(name="two_seats")
def two_seats_fixture() -> PassingGame:
    return a_match(TWO_SEATS, PLAIN_DECK, SEED)
