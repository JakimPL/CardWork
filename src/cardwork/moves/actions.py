from typing import Annotated, Literal

from pydantic import Field

from cardwork.decks.deck import Indices, NonEmptyIndices
from cardwork.models.base import BaseFrozen
from cardwork.moves.kind import ActionKind


class Action(BaseFrozen):
    """A seat's intent in the vocabulary of the table, as the client states it.

    An action names positions within a zone; turning those positions into effects is the rules' job.
    """


class Play(Action):
    kind: Literal[ActionKind.PLAY] = ActionKind.PLAY
    group: str
    indices: NonEmptyIndices


class Take(Action):
    kind: Literal[ActionKind.TAKE] = ActionKind.TAKE
    group: str
    indices: NonEmptyIndices


class Give(Action):
    kind: Literal[ActionKind.GIVE] = ActionKind.GIVE
    target_player: int = Field(ge=0)
    indices: NonEmptyIndices


class Reject(Action):
    kind: Literal[ActionKind.REJECT] = ActionKind.REJECT
    indices: NonEmptyIndices


class Discard(Action):
    kind: Literal[ActionKind.DISCARD] = ActionKind.DISCARD
    group: str
    indices: NonEmptyIndices


class Declare(Action):
    """A claim a seat makes about cards it holds, for the rules to confirm or refuse.

    `claim` is the game's own word for what is being claimed, which makes this the one intent carrying a word
    beside its cards: a claim states what the cards are held to be. `indices` names the cards it is made of,
    and an empty set makes it of the whole zone.
    """

    kind: Literal[ActionKind.DECLARE] = ActionKind.DECLARE
    claim: str
    indices: Indices


type AnyAction = Annotated[
    Play | Take | Give | Reject | Discard | Declare,
    Field(discriminator="kind"),
]
