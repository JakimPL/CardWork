from enum import StrEnum

from cardwork.combinations.combination import Combination
from cardwork.rounds.state import RoundState


class ClimbingPhase(StrEnum):
    """The phases a climbing round runs in, which stand beside the two `MatchPhase` keeps for the match.

    A round runs in two stages: a seat on lead puts down a combination of its own choosing, and the seats
    answering it climb over what stands on the table or pass. The round stands decided once a seat has played
    its last card, which the boundary beyond it scores.
    """

    LEAD = "lead"
    FOLLOW = "follow"
    DECIDED = "decided"


class ClimbingState(RoundState):
    """The cursor of a climbing match: the combination on the table, the seats that passed over it, who went out.

    `on_table` is the combination played last, carried as the ranking read it: its pattern, the cards it was made
    of and the place they took. So a seat answering it is held to what stands there rather than to a count of
    cards, and the whole contest is one reading the cursor already holds. It reads None on a lead, which is the
    turn a seat puts down a combination of its own choosing.

    `passed` holds the seats out of the contest the table stands in, which they stay out of while the combination
    on the table changes hands and take a turn in again once a lead reopens. `winner` names the seat that played
    its last card. The standing, the round in play and the clauses the match ends on stand on `RoundState`, which
    is where every match played in rounds keeps them.
    """

    on_table: Combination | None = None
    winner: int | None = None
    passed: frozenset[int] = frozenset()
