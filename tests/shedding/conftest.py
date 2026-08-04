import pytest

from cardgames.backend.shedding.game import ONE_ROUND, SheddingGame

from .driving import ROUNDS, SEATS, SEED, TWO_SEATS, a_match


@pytest.fixture(name="shedding")
def shedding_fixture() -> SheddingGame:
    return a_match(SEATS, ROUNDS, SEED)


@pytest.fixture(name="two_seats")
def two_seats_fixture() -> SheddingGame:
    return a_match(TWO_SEATS, ONE_ROUND, SEED)
