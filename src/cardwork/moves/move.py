from pydantic import Field

from cardwork.models.base import BaseFrozen
from cardwork.moves.actions import AnyAction


class Move(BaseFrozen):
    """A seat's intent, before the rules have had a say.

    Engine-initiated changes carry `Transaction.move = None`, which leaves every `Move` owned by a
    real seat.
    """

    player: int = Field(ge=0)
    action: AnyAction


Moves = tuple[Move, ...]
