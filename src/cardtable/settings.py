from pydantic import Field

from cardwork.models.base import BaseFrozen


class Settings(BaseFrozen):
    """What one table is opened with: the name it answers under, its seating, and how it deals and settles.

    A host holds these apart from the game itself, so the same settings open either game and the deck a
    game insists on stays that game's own business. A game plays the rounds it is given where its match runs
    to a count of them, and to a lead in points where it does not.
    """

    table: str = Field(min_length=1)
    players: int = Field(ge=2)
    rounds: int = Field(ge=1)
    seed: int
    grace_seconds: float = Field(ge=0.0)
