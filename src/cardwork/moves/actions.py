from typing import Annotated

from pydantic import Field

from cardwork.decks.deck import Indices
from cardwork.models.base import BaseFrozen

NonEmptyIndices = Annotated[Indices, Field(min_length=1, default_factory=set)]


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
