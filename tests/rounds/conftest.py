import pytest

from .demo import ROUNDS, SEED, TossGame, a_match


@pytest.fixture(name="toss")
def toss_fixture() -> TossGame:
    return a_match(TossGame, SEED, ROUNDS)
