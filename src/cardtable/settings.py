from random import SystemRandom
from typing import Final

from pydantic import Field

from cardwork.models.base import BaseFrozen
from cardwork.rounds.conclusion import Conclusion

SEEDS: Final[int] = 1 << 32


def a_drawn_seed() -> int:
    """A seed taken from the machine's own entropy, which is what deals a match no run has dealt before."""
    return SystemRandom().randrange(SEEDS)


class Settings(BaseFrozen):
    """What one table is opened with: the name it answers under, its seating, how long it runs and how it settles.

    A host holds these apart from the game itself, so the same settings open any game and the deck a game
    insists on stays that game's own business. The conclusion is where that reaches furthest: any match played
    in rounds runs to a count of them, to a score reached or to a lead held, so a table states the ending it
    wants of whichever game it seats.

    A table left to itself draws its own seed, so each run deals a match of its own. A run states one to deal
    a match it has dealt before, which is the seed the announcement names for exactly that purpose.
    """

    name: str = Field(min_length=1)
    players: int = Field(ge=2)
    conclusion: Conclusion
    seed: int = Field(default_factory=a_drawn_seed)
    grace_seconds: float = Field(ge=0.0)
