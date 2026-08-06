from typing import Protocol

from cardwork.decks.deck import Order
from cardwork.moves.move import Move
from cardwork.presentation.layout import Layout
from cardwork.states.state import StateT
from cardwork.transactions.journal import Journal
from cardwork.transactions.transaction import Transaction, Transactions
from cardwork.views.event import EventView
from cardwork.views.position import PositionView
from cardwork.zones.zone import ZoneId

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
    def players(self) -> int:
        """How many seats the table holds, which is the table a layout of it is built for."""

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

    def arrange(
        self,
        zone: ZoneId,
        order: Order,
        seat: int,
        base_seq: int,
    ) -> Transaction[StateT]:
        """Lay one of a seat's own zones out in the order it asks for, and hand back the record of it."""

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


class Presentation(Protocol):
    """Everything the adapter asks of a game's arrangement in order to serve it.

    A table reaches a screen as two answers: the projection of its cards, which the rules produce, and the
    layout an interface draws them into, which is stated apart from them. This is the whole of what a
    transport touches of the second, and it stands beside `Table` for the same reason — the port belongs to
    the consumer, which leaves the presentation layer free of any mention that a transport exists.

    `cardwork.presentation.Scene` satisfies it, and so does anything else a host holds a table's arrangement
    in: the layout of one observer is all that is asked for.
    """

    def layout(self, players: int, observer: int | None) -> Layout:
        """How a table of that many seats is laid out for one observer, or for a spectator holding none."""
