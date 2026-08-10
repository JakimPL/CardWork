from typing import Annotated, Final, Protocol

from pydantic import AfterValidator, Field

from cardserver.limits import NAME_LONGEST
from cardwork.decks.deck import Order
from cardwork.moves.move import Move
from cardwork.states.state import StateT
from cardwork.transactions.journal import Journal
from cardwork.transactions.transaction import Transaction, Transactions
from cardwork.views.event import EventView
from cardwork.views.position import PositionView
from cardwork.zones.zone import ZoneId

SEPARATORS: Final[frozenset[str]] = frozenset("/\\")
DOTTED: Final[frozenset[str]] = frozenset({".", ".."})


def a_table_name(offered: str) -> str:
    """The name with the space around it trimmed, held to what reads at a table and names one place alone.

    A name is a word a person is handed and a page carries in its own address, and a host is free to write a
    table down under a name of its own making. So a name reads plainly and names nothing but the table: the
    two separators and the two dotted names are the whole of what steps through a directory, and a name
    holding none of them is a name every route reaches, since a path stands between two slashes.

    Raises:
        ValueError: when nothing but space was offered, when a character of it shows nothing, or when it
            reads as a step through a directory rather than as a name.
    """
    read = offered.strip()
    if not read:
        raise ValueError("A name is what a table is read by, and this one holds nothing but space")

    if not read.isprintable():
        raise ValueError(f"A name reads at a table, and {offered!r} holds a character that shows nothing")

    if SEPARATORS & set(read) or read in DOTTED:
        raise ValueError(f"A name reads at a table rather than through a directory, and {offered!r} steps through one")

    return read


TableId = Annotated[str, Field(min_length=1, max_length=NAME_LONGEST), AfterValidator(a_table_name)]


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
