from collections.abc import Mapping
from typing import Generic

from cardwork.models.base import BaseFrozen
from cardwork.moves.move import Moves
from cardwork.states.state import StateT
from cardwork.views.zone import ZoneView
from cardwork.zones.zone import ZoneId


class PositionView(BaseFrozen, Generic[StateT]):
    """Everything one observer is entitled to know about a position.

    This is the only shape that crosses the wire, which makes it the single place where the server's
    knowledge is narrowed to one seat's entitlement.

    `legal` holds the moves this observer may make from the position, which is what an interface reads to
    offer a move and to refuse one before it is sent. It arrives with the sequence it belongs to, so the
    moves a client weighs and the `base_seq` it quotes name one position.
    """

    observer: int | None
    seq: int
    zones: Mapping[ZoneId, ZoneView]
    state: StateT
    legal: Moves
