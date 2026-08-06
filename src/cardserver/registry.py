from cardserver.errors import UnknownTable
from cardserver.protocol import Presentation, Table, TableId
from cardserver.sessions import InService, TableSession
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

    def __init__(self, grace_seconds: float) -> None:
        self._sessions: dict[TableId, InService] = {}
        self._grace_seconds = grace_seconds

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

    async def close(self) -> None:
        """Drop every timer still in hand, which is what ends service cleanly."""
        for session in self._sessions.values():
            await session.close()
