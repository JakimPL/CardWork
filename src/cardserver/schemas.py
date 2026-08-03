from pydantic import Field

from cardwork.models.base import BaseFrozen
from cardwork.moves.move import Move


class MoveRequest(BaseFrozen):
    """A command as a client sends it: the intent, the position it was built on, and a name for the try.

    Repeating the key names the same attempt, so a client that retries a request it never saw answered
    lands its move once.
    """

    move: Move
    base_seq: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1)


class MoveAccepted(BaseFrozen):
    """The sequence a command was committed at, which the client quotes as `base_seq` for its next one."""

    seq: int


class ErrorBody(BaseFrozen):
    """A refusal in the shape a client can act on: what kind it was, and what the server made of it.

    The kind is the name of the rule that refused, which lets a client branch on the answer while the
    detail stays a sentence for a person to read.
    """

    error: str
    detail: str
