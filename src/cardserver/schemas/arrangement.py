from pydantic import Field

from cardwork.decks.deck import Order
from cardwork.models.base import BaseFrozen
from cardwork.zones.zone import ZoneId


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
