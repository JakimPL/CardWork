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
