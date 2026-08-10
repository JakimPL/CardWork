from collections.abc import Callable, Mapping
from time import monotonic

from cardserver.errors import TableTaken, UnknownTable
from cardserver.protocols.presentation import Presentation
from cardserver.protocols.table import Table, TableId
from cardserver.remembering import Remembering
from cardserver.sessions.in_service import InService
from cardserver.sessions.table import TableSession
from cardwork.states.state import GameState
from cardwork.transactions.transaction import Transactions


class TableRegistry:
    """Every table this server holds, each with the single writer that serves it.

    The host application opens tables, since building one means knowing a game and this adapter is
    written for none in particular. Serving them means finding one by name and handing it the request.

    A table settles the shape of its own cursor as it opens and holds it inside, so one registry serves
    games whose states are of different shapes and a table found by name answers as a table in service.

    Tables run fully concurrently: the lock a session holds is its own, so a command at one table waits
    on nothing happening at another.
    """

    def __init__(
        self,
        grace_seconds: float,
        *,
        keeping: Remembering,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._sessions: dict[TableId, InService] = {}
        self._grace_seconds = grace_seconds
        self._keeping = keeping
        self._clock = clock

    def open[StateT: GameState](
        self,
        table_id: TableId,
        table: Table[StateT],
        presentation: Presentation,
    ) -> TableSession[StateT]:
        """Put a game into service under a name, and hand back the session that will carry it.

        A table opens at the position its deal left it in, and the rules are next asked for anything
        once a seat has acted. It opens with the arrangement it is read through besides, since a client
        joining asks for both and the host holding the game holds the layout of it too.

        The record of it is opened as the table is, so a table stands written down from its deal onward and
        the whole of what a company has played survives whatever becomes of the process serving it.

        Raises:
            TableTaken: when a table of that name is already in service, which would leave the record
                a client was reading replaced under it.
        """
        session = self._served(table_id, table, presentation)
        session.keep()
        return session

    def reopen[StateT: GameState](
        self,
        table_id: TableId,
        table: Table[StateT],
        presentation: Presentation,
        *,
        applied: Mapping[str, int],
        settled: Transactions[StateT],
    ) -> TableSession[StateT]:
        """Put a table read back from its own record into service, holding the attempts it already answered.

        A table opened this way stands where its last commit left it, so the company reaches the game they
        were playing rather than a fresh deal of it. What is written down stands as it was written: the record
        already holds this table, and the commits it opens owing are the next lines of it.

        Raises:
            TableTaken: when a table of that name is already in service, which reading one record twice
                would otherwise leave replaced under the company playing it.
        """
        session = self._served(table_id, table, presentation)
        session.restore(applied, settled)
        return session

    def session(self, table_id: TableId) -> InService:
        """The session serving one table.

        Raises:
            UnknownTable: when no table of that name is in service.
        """
        session = self._sessions.get(table_id)
        if session is None:
            raise UnknownTable(table_id)

        return session

    def sessions(self) -> tuple[tuple[TableId, InService], ...]:
        """Every table in service, which is what overseeing reads the played half of the lobby by."""
        return tuple(self._sessions.items())

    def serving(self) -> int:
        """How many tables are in service, which a cap on the lobby counts beside the tables still gathering."""
        return len(self._sessions)

    def idle(self, idle: float, now: float) -> tuple[TableId, ...]:
        """The tables nobody is at that have stood too long, which is what a reaper comes to clear away.

        A table is idle once the clock has run past the allowance since the last commit landed on it or the
        last stream was taken up on it, so a game a company left mid-play and one broken up and left to be
        forgotten both fall due to be cleared, while a company still turning a hand over keeps their table.
        """
        return tuple(table for table, session in self._sessions.items() if now - session.touched > idle)

    async def dismiss(self, table_id: TableId, reason: str | None) -> None:
        """Break one table up and forget it, so its seats learn the game is over and its name comes free again.

        The session is woken before it is dropped, since the streams still on it hold it themselves and read it
        closed to carry their last word; what forgetting it does is leave a client reconnecting to find the
        table gone rather than the game going on without it. The record kept of it goes the same way, so a
        table broken up stays broken up across a restart.

        Raises:
            UnknownTable: when no table of that name is in service.
        """
        await self.session(table_id).dismiss(reason)
        self._sessions.pop(table_id, None)
        self._keeping.forget(table_id)

    async def close(self) -> None:
        """Drop every timer still in hand, which is what ends service cleanly."""
        for session in self._sessions.values():
            await session.close()

    def _served[StateT: GameState](
        self,
        table_id: TableId,
        table: Table[StateT],
        presentation: Presentation,
    ) -> TableSession[StateT]:
        """Hold one game under a name with the writer that will serve it, however the run came to have it.

        A table dealt here and a table read back from a record are the same table to everything that serves
        it, so they are built the same way and told apart by what each says to the store: a deal writes the
        record it opens, and a table read back is already written down.

        Raises:
            TableTaken: when a table of that name is already in service.
        """
        if table_id in self._sessions:
            raise TableTaken(table_id)

        session = TableSession(
            table_id,
            table,
            presentation,
            keeping=self._keeping,
            grace_seconds=self._grace_seconds,
            clock=self._clock,
        )
        self._sessions[table_id] = session
        return session
