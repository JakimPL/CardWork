from random import SystemRandom
from typing import Final

from pydantic import Field

from cardwork.models.base import BaseFrozen

SEEDS: Final[int] = 1 << 32


def a_drawn_seed() -> int:
    """A seed taken from the machine's own entropy, which is what deals a match no run has dealt before."""
    return SystemRandom().randrange(SEEDS)


class Settings(BaseFrozen):
    """What one table is opened with: the name it answers under, its seating, and how it deals and settles.

    A host holds these apart from the game itself, so the same settings open either game and the deck a
    game insists on stays that game's own business. A game plays the rounds it is given where its match runs
    to a count of them, and to a lead in points where it does not.

    A table left to itself draws its own seed, so each run deals a match of its own. A run states one to deal
    a match it has dealt before, which is the seed the announcement names for exactly that purpose.
    """

    name: str = Field(min_length=1)
    players: int = Field(ge=2)
    rounds: int = Field(ge=1)
    seed: int = Field(default_factory=a_drawn_seed)
    grace_seconds: float = Field(ge=0.0)
