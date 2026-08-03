from typing import Generic

from cardwork.cards.game import GameCard
from cardwork.models.base import BaseFrozen
from cardwork.moves.actions import AnyAction
from cardwork.moves.move import Moves
from cardwork.states.state import StateT
from cardwork.zones.zone import ZoneId


class MoveView(BaseFrozen):
    """The move behind a commit, narrowed to what one observer may know of it.

    The acting seat reaches the whole table, since a turn being taken is public. The action itself
    reaches the seat that made it, whose own zones already spell out the positions it named; every
    other observer learns the same thing from the zone changes, at the resolution they are owed.
    """

    player: int
    action: AnyAction | None


class ZoneChange(BaseFrozen):
    """How one zone read before a commit and how it reads after, both as this observer sees them.

    Carrying both sides lets a client apply the change against what it already holds, and keeps a
    change to concealed cards down to the count and the positions it occupies.
    """

    zone: ZoneId
    before: tuple[GameCard | None, ...]
    after: tuple[GameCard | None, ...]


class EventView(BaseFrozen, Generic[StateT]):
    """One commit as it reaches one observer: who acted, what it changed for them, and the cursor it left.

    An event carries the knowledge a position view would have carried, so a client that joined at a
    known sequence number stays current from the stream alone, and one rule governs both shapes.

    `legal` holds the moves open to this observer once the commit has landed, which the table stands `seq + 1`
    commits into and is what a client quotes as `base_seq` for one of them. Carrying them here is what lets a
    client read the stream and know its options from it, rather than asking after each commit and racing the
    next one.
    """

    seq: int
    observer: int | None
    move: MoveView | None
    changes: tuple[ZoneChange, ...]
    state: StateT
    legal: Moves
