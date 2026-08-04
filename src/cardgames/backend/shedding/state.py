from enum import StrEnum

from cardwork.rounds.state import RoundState


class SheddingPhase(StrEnum):
    """The phase a shedding round runs in, which stands beside the two `MatchPhase` keeps for the match.

    A round runs in one stage: the turn stands with a seat that may shed or draw, and the round stands decided
    once a seat has gone out or the stock has run out with no seat holding a set. The boundary finds it decided,
    scores it, and deals the next.
    """

    SHEDDING = "shedding"
    DECIDED = "decided"


class SheddingState(RoundState):
    """The cursor of a shedding match: who went out.

    `winner` names the seat that shed its last card, and reads None through a round in play and through a round
    the stock ran out of. What the round awarded stands in `round_points`, which is read off the hands as they
    lie, so a round closed on an exhausted stock is scored as fully as one a seat went out of.

    The standing, the round in play and the clauses the match ends on stand on `RoundState`, which is where every
    match played in rounds keeps them.
    """

    winner: int | None = None
