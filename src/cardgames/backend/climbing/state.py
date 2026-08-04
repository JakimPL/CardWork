from collections import defaultdict

from cardwork.rounds.state import RoundState


class ClimbingState(RoundState):
    scores: defaultdict[int, int]
    winner: int | None = None
