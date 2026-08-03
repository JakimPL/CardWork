from enum import StrEnum
from typing import Final, TypeVar

from cardwork.states.state import GameState, Points

BEFORE_THE_FIRST_ROUND: Final[int] = 0


class MatchPhase(StrEnum):
    """The two phases this layer runs the table in, which stand beside the phases a game names for its rounds.

    A phase is one field, and two vocabularies read against it: these, and the `StrEnum` a game declares for the
    stages of its own round. A member carries its value, so `match` reads either one against the state exactly as
    it arrives from the journal or the wire.
    """

    BETWEEN_ROUNDS = "between_rounds"
    MATCH_OVER = "match_over"


class RoundState(GameState):
    """The cursor of a match played in rounds: which round is running, the seat leading it, what it scores.

    Two tallies stand side by side. `points` is the score of record, the one a match is won on; `round_points`
    is what the round in play has scored so far, which is added into `points` as the round closes. So a client
    reads both the standing and the round it is watching.

    `round_number` counts the rounds that have opened, standing at `BEFORE_THE_FIRST_ROUND` on a table whose
    first round has yet to be dealt, and `leader` names the seat the round in play opened on. The phase reads as
    a `MatchPhase` while the match stands between rounds or at its close, and as one of the game's own while a
    round is in play.

    A game declares its own subclass for whatever else its rounds track — the turn within one, the seat that
    declared a win, the number of rounds the match was built for.
    """

    round_number: int = BEFORE_THE_FIRST_ROUND
    leader: int | None = None
    round_points: Points = ()

    @property
    def led_by(self) -> int:
        """The seat leading the round in play.

        Raises:
            ValueError: when no round has opened, which leaves no seat leading one.
        """
        if self.leader is None:
            raise ValueError("No round has opened, so no seat leads one")

        return self.leader


RoundStateT = TypeVar("RoundStateT", bound=RoundState)
