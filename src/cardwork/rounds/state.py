from enum import StrEnum
from typing import Final, TypeVar

from pydantic import Field

from cardwork.rounds.conclusion import ONE_POINT, ONE_ROUND
from cardwork.states.award import Award
from cardwork.states.state import GameState, Points

BEFORE_THE_FIRST_ROUND: Final[int] = 0
USUAL_AWARD: Final[Award] = Award.HIGHEST
TWO_SEATS: Final[int] = 2


class MatchPhase(StrEnum):
    """The two phases this layer runs the table in, which stand beside the phases a game names for its rounds.

    A phase is one field, and two vocabularies read against it: these, and the `StrEnum` a game declares for the
    stages of its own round. A member carries its value, so `match` reads either one against the state exactly as
    it arrives from the journal or the wire.
    """

    BETWEEN_ROUNDS = "between_rounds"
    MATCH_OVER = "match_over"


class RoundState(GameState):
    """The cursor of a match played in rounds: which round is running, the seat leading it, what it scores, where
    it ends.

    Two tallies stand side by side. `points` is the score of record, the one a match is won on; `round_points`
    is what the round in play has scored so far, which is added into `points` as the round closes. So a client
    reads both the standing and the round it is watching.

    `round_number` counts the rounds that have opened, standing at `BEFORE_THE_FIRST_ROUND` on a table whose
    first round has yet to be dealt, and `leader` names the seat the round in play opened on. The phase reads as
    a `MatchPhase` while the match stands between rounds or at its close, and as one of the game's own while a
    round is in play.

    **The ending stands on the cursor as well.** `award` is the end of the standing this match is won at, which is
    a rule of the game and stamped by it; `rounds`, `target` and `lead` are the clauses it ends on, which a table
    states as the `Conclusion` it is opened with. Keeping them here leaves a replayed position self-describing:
    how long this table was ever going to run, and which seat it would belong to, are read from the record as
    everything else about it is.

    A game declares its own subclass for whatever else its rounds track — the turn within one, the seat that
    declared a win.
    """

    round_number: int = BEFORE_THE_FIRST_ROUND
    leader: int | None = None
    round_points: Points = ()
    award: Award = USUAL_AWARD
    rounds: int | None = Field(default=None, ge=ONE_ROUND)
    target: int | None = Field(default=None, ge=ONE_POINT)
    lead: int | None = Field(default=None, ge=ONE_POINT)

    @property
    def led_by(self) -> int:
        """The seat leading the round in play.

        Raises:
            ValueError: when no round has opened, which leaves no seat leading one.
        """
        if self.leader is None:
            raise ValueError("No round has opened, so no seat leads one")

        return self.leader

    def concluded(self, standing: Points) -> bool:
        """Whether the clauses this match ends on are met by the standing as it stands.

        A match stating several clauses ends on the first of them the standing meets. A cursor carrying none of
        them is one whose game states its ending for itself, and is read as a match still to be played out.

        Args:
            standing: what every seat holds, of two seats or more where the match ends on a lead.
        """
        return self._rounds_played() or self._target_reached(standing) or self._lead_held(standing)

    def _rounds_played(self) -> bool:
        """Whether the match has played the rounds it runs to."""
        return self.rounds is not None and self.round_number >= self.rounds

    def _target_reached(self, standing: Points) -> bool:
        """Whether some seat holds the score the match runs to, which either end of the standing climbs towards."""
        return self.target is not None and max(standing) >= self.target

    def _lead_held(self, standing: Points) -> bool:
        """Whether the seat at the winning end of the standing leads the next best by the margin the match runs to.

        Args:
            standing: what every seat holds, read from the winning end so that the two seats compared are the one
                holding the match and the one nearest to taking it.
        """
        if self.lead is None:
            return False

        leading, chasing = sorted(standing, reverse=self.award == Award.HIGHEST)[:TWO_SEATS]
        return abs(leading - chasing) >= self.lead


RoundStateT = TypeVar("RoundStateT", bound=RoundState)
