from typing import Final

from cardserver.protocols import TableId
from cardserver.remembering import Kept, RoomRecord, TableRecord, Written
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.transactions.journal import Journal

WRITTEN_AT: Final[float] = 0.0
ROOM: Final[str] = "room"
JOURNAL: Final[str] = "journal"
COMMIT: Final[str] = "commit"
FORGOTTEN: Final[str] = "forgotten"
ASIDE: Final[str] = "aside"
CLOSED: Final[str] = "closed"


def read_back(record: TableRecord) -> tuple[Written[GameState], ...]:
    """Every line of a table's record as the commit it holds and the key a client landed that commit under.

    The lines cross the seam as text and are read here by the state the demo game declares, which is the whole
    of what a host holding the rules does with them.
    """
    return tuple(Written[GameState].model_validate_json(line) for line in record.commits)


def a_journal(record: TableRecord) -> Journal[GameState]:
    """The record kept of one table read back as a journal, which is what a run resuming it hands the rules."""
    return Journal[GameState](
        initial=Position[GameState].model_validate_json(record.origin),
        transactions=tuple(written.transaction for written in read_back(record)),
    )


def applied_of(record: TableRecord) -> dict[str, int]:
    """The sequence each client's attempt reached, which is what a table read back answers a retry from."""
    return {written.key: written.transaction.seq for written in read_back(record) if written.key is not None}


class Keeping:
    """A store held in memory, which is what lets a test read back whatever a room or a table wrote down.

    Everything is kept in the shape the port hands it over in — the room whole, the table a line at a time —
    so a test reads the record exactly as a store on disk would find it. What arrived is kept in order
    besides, which is what a test reads to say the deal wrote the table down before the room that names it
    dealt: a run reading these back takes a journal for the mark a deal leaves.
    """

    def __init__(self) -> None:
        self.rooms: dict[TableId, RoomRecord] = {}
        self.origins: dict[TableId, str] = {}
        self.commits: dict[TableId, list[str]] = {}
        self.forgotten: list[TableId] = []
        self.aside: list[TableId] = []
        self.order: list[str] = []

    @property
    def writes(self) -> int:
        """How many times a room has been written down, which counts the changes a lobby wrote through."""
        return self.order.count(ROOM)

    def remember_room(self, record: RoomRecord) -> None:
        """Write one room down as it stands, over whatever stood written before."""
        self.rooms[record.table] = record
        self.order.append(ROOM)

    def open_journal(self, table: TableId, origin: str) -> None:
        """Open the record of one table at the origin its journal stands on."""
        self.origins[table] = origin
        self.commits[table] = []
        self.order.append(JOURNAL)

    def append(self, table: TableId, line: str) -> None:
        """Lay one commit into the record of a table, after every commit already down."""
        self.commits[table].append(line)
        self.order.append(COMMIT)

    def forget(self, table: TableId) -> None:
        """Drop everything written down of one table, and say so for a test to read."""
        self.rooms.pop(table, None)
        self.origins.pop(table, None)
        self.commits.pop(table, None)
        self.forgotten.append(table)
        self.order.append(FORGOTTEN)

    def set_aside(self, table: TableId) -> None:
        """Set the record of one table aside, which leaves it where a test reads what was set aside."""
        self.aside.append(table)
        self.order.append(ASIDE)

    def written(self, table: TableId) -> TableRecord:
        """The record kept of one table in service, which a test reads back the way a run resuming it does.

        Raises:
            KeyError: when no table of that name has been written down.
        """
        return TableRecord(origin=self.origins[table], commits=tuple(self.commits[table]))

    def kept(self) -> tuple[Kept, ...]:
        """Everything written down here, in the shape a run gathers its lobby back from."""
        return tuple(
            Kept(
                room=room,
                table=self._table_of(table),
                updated=WRITTEN_AT,
            )
            for table, room in self.rooms.items()
        )

    def close(self) -> None:
        """Let go of a store held in memory, which is a word a test hears and a record of nothing."""
        self.order.append(CLOSED)

    def _table_of(self, table: TableId) -> TableRecord | None:
        """The record kept of one table in service, and none for a room still gathering."""
        origin = self.origins.get(table)
        if origin is None:
            return None

        return TableRecord(origin=origin, commits=tuple(self.commits[table]))
