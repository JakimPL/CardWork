from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from cardwork.cards.deck import Indices

NonEmptyIndices = Annotated[Indices, Field(min_length=1, default_factory=set)]


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Play(Action):
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
