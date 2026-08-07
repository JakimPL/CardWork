from collections.abc import Callable
from time import monotonic

from cardserver.errors import UnknownTable
from cardserver.protocols.presentation import Presentation
from cardserver.protocols.table import Table, TableId
from cardserver.sessions.in_service import InService
from cardserver.sessions.table import TableSession
from cardwork.states.state import GameState


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
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._sessions: dict[TableId, InService] = {}
        self._grace_seconds = grace_seconds
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

        Raises:
            ValueError: when a table of that name is already in service, which would leave the record
                a client was reading replaced under it.
        """
        if table_id in self._sessions:
            raise ValueError(f"A table named {table_id!r} is already in service")

        session = TableSession(
            table_id,
            table,
            presentation,
            self._grace_seconds,
            self._clock,
        )
        self._sessions[table_id] = session
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
        """The tables no seat has committed to in too long, which is what a reaper comes to clear away.

        A table is idle once the clock has run past the allowance since its last commit, so a game a company
        left mid-play and one broken up and left to be forgotten both fall due to be cleared.
        """
        return tuple(table for table, session in self._sessions.items() if now - session.touched > idle)

    async def dismiss(self, table_id: TableId, reason: str | None) -> None:
        """Break one table up and forget it, so its seats learn the game is over and its name comes free again.

        The session is woken before it is dropped, since the streams still on it hold it themselves and read it
        closed to carry their last word; what forgetting it does is leave a client reconnecting to find the
        table gone rather than the game going on without it.

        Raises:
            UnknownTable: when no table of that name is in service.
        """
        await self.session(table_id).dismiss(reason)
        self._sessions.pop(table_id, None)

    async def close(self) -> None:
        """Drop every timer still in hand, which is what ends service cleanly."""
        for session in self._sessions.values():
            await session.close()
