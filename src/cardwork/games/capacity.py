from typing import Annotated, Final, Self

from pydantic import Field, model_validator

from cardwork.exceptions import GameValidationError
from cardwork.models.base import BaseFrozen

ONE_SEAT: Final[int] = 1


class Capacity(BaseFrozen):
    """The tables a game is played at: the fewest seats it needs and the most it holds.

    A game states its seating as a declaration rather than a check, so the range a reader looks for stands
    beside the vocabulary the game is played with, and the engine holds every table it opens to it:

        capacity: ClassVar[Capacity] = Capacity(least=2, most=5)

    A game played at one size states that size as both. A game bounded by the cards it deals states the
    table its deck reaches, since a seating range is something a game has settled rather than discovered.
    """

    least: Annotated[int, Field(ge=ONE_SEAT)]
    most: Annotated[int, Field(ge=ONE_SEAT)]

    @model_validator(mode="after")
    def _a_table_holds_the_seats_it_needs(self) -> Self:
        if self.most < self.least:
            raise ValueError(
                f"A game needing {self.least} seats holds that many or more, and this one holds {self.most}"
            )

        return self

    def admits(self, players: int) -> bool:
        """Whether a table of that many seats is one this game is played at."""
        return self.least <= players <= self.most

    def confirm(self, players: int) -> None:
        """Confirm a table of that many seats is one this game is played at.

        Raises:
            GameValidationError: when this game seats a table of another size.
        """
        if not self.admits(players):
            raise GameValidationError(f"This game seats {self._spoken()}, and {players} were asked for")

    def _spoken(self) -> str:
        """The seating as a phrase, which is how a refusal states the table a game is played at."""
        if self.least == self.most:
            return f"{self.least} players"

        return f"{self.least} to {self.most} players"
