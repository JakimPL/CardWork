from enum import StrEnum
from typing import Final

from cardwork.rounds.state import RoundState

BEFORE_THE_FIRST_TURN: Final[int] = 0


class ShowdownPhase(StrEnum):
    """The phase a showdown round runs in, which stands beside the two `MatchPhase` keeps for the match.

    A round runs in one stage, since a turn is a single simultaneous commitment: every seat seals a card, and
    the settlement following the last of them turns the cards over, scores the turn and opens the next.
    """

    COMMITTING = "committing"


class ShowdownState(RoundState):
    """The cursor of a showdown match: the turn the round has reached, and the rounds the match was built for.

    `turn_number` names the turn in play, standing at `BEFORE_THE_FIRST_TURN` on a table whose first round has
    yet to be dealt and at the last turn of a round once that turn has been revealed.

    Keeping the match length here leaves a replayed position self-describing: how many rounds this table was
    ever going to play is read from the state, as everything else about it is.
    """

    rounds: int
    turn_number: int = BEFORE_THE_FIRST_TURN
