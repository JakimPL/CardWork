from enum import StrEnum

from cardwork.rounds.state import RoundState


class ClimbingPhase(StrEnum):
    LEAD = "lead"
    FOLLOW = "follow"
    DECIDED = "decided"


class ClimbingState(RoundState):
    combination_size: int | None = None
    winner: int | None = None
    passed: frozenset[int] = frozenset()
