from random import Random
from typing import Final

import pytest

from .demo import DECK, SEATS, DiscardGame, SealedRoundGame

SEED: Final[int] = 20260802


@pytest.fixture(name="game")
def game_fixture() -> DiscardGame:
    return DiscardGame(players=SEATS, deck=DECK, rng=Random(SEED))


@pytest.fixture(name="sealed")
def sealed_fixture() -> SealedRoundGame:
    return SealedRoundGame(players=SEATS, deck=DECK, rng=Random(SEED))
