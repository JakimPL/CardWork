from random import Random
from typing import Final

from cardwork.decks.draw import permutation

SIZE: Final[int] = 12
SHARED_SEED: Final[int] = 7


def test_permutation_reorders_every_position_exactly_once(rng: Random) -> None:
    order = permutation(SIZE, rng)

    assert sorted(order) == list(range(SIZE))


def test_permutation_repeats_for_generators_seeded_alike() -> None:
    assert permutation(SIZE, Random(SHARED_SEED)) == permutation(SIZE, Random(SHARED_SEED))


def test_permutation_of_an_empty_run_is_empty(rng: Random) -> None:
    assert permutation(0, rng) == ()
