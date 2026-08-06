from random import SystemRandom
from typing import Final

from pydantic import Field, field_validator

from cardserver.codes import a_drawn_code, ranks_in, written
from cardwork.models.base import BaseFrozen

SEEDS: Final[int] = 1 << 32


def a_drawn_seed() -> int:
    """A seed taken from the machine's own entropy, which is what deals a match no run has dealt before."""
    return SystemRandom().randrange(SEEDS)


class Settings(BaseFrozen):
    """What one table is opened with: the name it answers under, the code it gathers on, and how long it runs.

    A host holds these apart from the game itself, so the same settings gather any game and what is played stays
    the company's own business: the seating, the decks and the ending are settled at the gathering and reach the
    host as a choice.

    A table left to itself draws its own seed and its own code, so each run deals a match of its own and gathers
    behind a hand of ranks nobody has been handed before. A run states a seed to deal a match it has dealt
    before, which is the seed the announcement names for exactly that purpose, and states a code to gather at an
    address it has handed out already.
    """

    name: str = Field(min_length=1)
    code: str = Field(default_factory=a_drawn_code)
    seed: int = Field(default_factory=a_drawn_seed)
    grace_seconds: float = Field(ge=0.0)

    @field_validator("code")
    @classmethod
    def _a_code_is_a_hand_of_ranks(cls, offered: str) -> str:
        """The code as the ranks it reads as, which is the one form a person is handed and a page offers back.

        Raises:
            ValueError: when what was stated reads as no hand of ranks at all.
        """
        ranks = ranks_in(offered)
        if ranks is None:
            raise ValueError(f"A table gathers on a hand of ranks, and {offered!r} reads as none")

        return written(ranks)
