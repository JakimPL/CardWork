from pydantic import Field

from cardwork.decks.deck import Order
from cardwork.models.base import BaseFrozen
from cardwork.moves.move import Move
from cardwork.zones.zone import ZoneId


class MoveRequest(BaseFrozen):
    """A command as a client sends it: the intent, the position it was built on, and a name for the try.

    Repeating the key names the same attempt, so a client that retries a request it never saw answered
    lands its move once.
    """

    move: Move
    base_seq: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1)


class ArrangementRequest(BaseFrozen):
    """A seat laying a zone of its own out: the zone, the run it comes to lie in, and the position it was read at.

    The seat asking is the one thing this leaves out, since the server reads it off the credential: a client
    states which of its zones it is sorting and never whose zone that is.

    `order` names the positions the zone holds in the order they come to lie, so the first of them is the card
    that comes to lie first. Repeating the key names the same attempt, so a client that retries a request it
    never saw answered lands its order once.
    """

    zone: ZoneId
    order: Order
    base_seq: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1)


class CommandAccepted(BaseFrozen):
    """The sequence a command was committed at, which the table stands one commit past.

    A client holding this commit stands at `seq + 1` commits, and that count is what its next command quotes
    as `base_seq`. A move and an arrangement are answered alike, since what either of them leaves behind is
    one commit in the record every seat reads.
    """

    seq: int


class ErrorBody(BaseFrozen):
    """A refusal in the shape a client can act on: what kind it was, and what the server made of it.

    The kind is the name of the rule that refused, which lets a client branch on the answer while the
    detail stays a sentence for a person to read.
    """

    error: str
    detail: str
