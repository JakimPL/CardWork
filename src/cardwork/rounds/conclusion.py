from typing import Final, Self

from pydantic import Field, model_validator

from cardwork.models.base import BaseFrozen

ONE_ROUND: Final[int] = 1
ONE_POINT: Final[int] = 1


class Conclusion(BaseFrozen):
    """How long a match runs: the clauses it ends on, of which a match states at least one.

    A match ends on a count of rounds played, on a score some seat reaches, or on a lead one seat opens over the
    next best, and a table states whichever of those the match it opens is played to. Several stated together end
    it on the first of them the standing meets, which is how a match runs to five hundred points or ten rounds,
    whichever arrives first.

    | clause | ends the match once |
    |---|---|
    | `rounds` | that many rounds have been played |
    | `target` | some seat holds that score, whether reaching it wins the match or loses it |
    | `lead` | the seat at the winning end of the standing leads the next best by that margin |

    This is what a table is opened with, and the clauses it states are stamped onto the cursor the table opens on,
    so a replayed position describes the ending it was always running to. `RoundState` carries them there and
    reads them as `concluded`.
    """

    rounds: int | None = Field(default=None, ge=ONE_ROUND)
    target: int | None = Field(default=None, ge=ONE_POINT)
    lead: int | None = Field(default=None, ge=ONE_POINT)

    @model_validator(mode="after")
    def _a_match_states_where_it_ends(self) -> Self:
        """Confirm the match has an ending to reach.

        Raises:
            ValueError: when no clause is stated, which leaves a match running for as long as it is played.
        """
        if self.rounds is None and self.target is None and self.lead is None:
            raise ValueError(
                "A match ends on a count of rounds, a score reached or a lead held, and states at least one"
            )

        return self
