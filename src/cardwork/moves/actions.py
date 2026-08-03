from typing import Annotated, Literal

from pydantic import Field

from cardwork.decks.deck import NonEmptyIndices
from cardwork.models.base import BaseFrozen


class Action(BaseFrozen):
    """A seat's intent in the vocabulary of the table, as the client states it.

    An action names positions within a zone; turning those positions into effects is the rules' job,
    which is what keeps the same five intents serving games that disagree about their meaning.
    """


class Play(Action):
    kind: Literal["play"] = "play"
    group: str
    indices: NonEmptyIndices


class Take(Action):
    kind: Literal["take"] = "take"
    group: str
    indices: NonEmptyIndices


class Give(Action):
    kind: Literal["give"] = "give"
    target_player: int = Field(ge=0)
    indices: NonEmptyIndices


class Reject(Action):
    kind: Literal["reject"] = "reject"
    indices: NonEmptyIndices


class Discard(Action):
    kind: Literal["discard"] = "discard"
    group: str
    indices: NonEmptyIndices


type AnyAction = Annotated[
    Play | Take | Give | Reject | Discard,
    Field(discriminator="kind"),
]
