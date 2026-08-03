from typing import Protocol

from cardwork.moves.move import Move
from cardwork.states.state import StateT
from cardwork.transactions.journal import Journal
from cardwork.transactions.transaction import Transaction, Transactions
from cardwork.views.event import EventView
from cardwork.views.position import PositionView

TableId = str


class Table(Protocol[StateT]):
    """Everything the adapter asks of a game in order to serve it, and the whole of what it may touch.

    The port lives with the consumer that needs it: the engine is written for the table alone, and this
    states which part of its surface a transport depends on. A game satisfies it by having the methods,
    which leaves `cardwork` free of any mention that an adapter exists.

    The state type stays exact, so a server built for one rule set carries that game's own state
    through the projections it serves and out to the wire with every declared field intact.
    """

    @property
    def head(self) -> int:
        """How many commits the table holds, which is the sequence the next one takes."""

    @property
    def journal(self) -> Journal[StateT]:
        """The table's full record, cards and all, for analysis once the game is over."""

    def submit(
        self,
        move: Move,
        base_seq: int,
    ) -> Transaction[StateT]:
        """Commit one seat's move against the position it names, and hand back the record of it."""

    def settle(self) -> Transactions[StateT]:
        """Commit whatever the rules still owe, until the table comes to rest."""

    def view(self, observer: int | None) -> PositionView[StateT]:
        """The table as one observer is entitled to see it."""

    def events(
        self,
        observer: int | None,
        since: int,
    ) -> tuple[EventView[StateT], ...]:
        """Every commit from `since` onward as one observer learns of it, in commit order."""

    def mark_published(self) -> None:
        """Close every commit the table holds to undo, which is what serving one of them makes true."""
