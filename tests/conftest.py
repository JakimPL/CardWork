from random import Random
from typing import Final

import pytest

SEED: Final[int] = 0


@pytest.fixture(name="rng")
def rng_fixture() -> Random:
    return Random(SEED)
