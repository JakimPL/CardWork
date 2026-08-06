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
    """The cursor of a showdown match: the turn the round has reached.

    `turn_number` names the turn in play, standing at `BEFORE_THE_FIRST_TURN` on a table whose first round has
    yet to be dealt and at the last turn of a round once that turn has been revealed.

    The standing, the round in play and the clauses the match ends on stand on `RoundState`, which is where every
    match played in rounds keeps them.
    """

    turn_number: int = BEFORE_THE_FIRST_TURN
