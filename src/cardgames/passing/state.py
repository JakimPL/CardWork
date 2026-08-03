from enum import StrEnum

from cardwork.rounds.state import RoundState


class PassingPhase(StrEnum):
    """The phases a passing round runs in, which stand beside the two `MatchPhase` keeps for the match.

    A round passes cards while a seat holds the turn, and stands decided once a claim has been confirmed or
    the pile has run out. The boundary finds it decided, scores it, and deals the next.
    """

    PASSING = "passing"
    DECIDED = "decided"


class PassingState(RoundState):
    """The cursor of a passing match: what the seat on turn has spent its turn on, and who won the round.

    `swapped` states that the seat on turn has made the one exchange a turn admits, and reads False again as
    the turn passes on. `winner` names the seat whose claim the rules confirmed, and reads None through a
    round in play and through a round the pile ran out on.
    """

    swapped: bool = False
    winner: int | None = None
