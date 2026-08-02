from cardwork.decks.deck import NonEmptyIndices
from cardwork.models.base import BaseFrozen


class Action(BaseFrozen):
    pass


class Play(Action):
    group: str
    indices: NonEmptyIndices


class Take(Action):
    group: str
    indices: NonEmptyIndices


class Give(Action):
    target_player: int
    indices: NonEmptyIndices


class Reject(Action):
    indices: NonEmptyIndices


class Discard(Action):
    group: str
    indices: NonEmptyIndices
