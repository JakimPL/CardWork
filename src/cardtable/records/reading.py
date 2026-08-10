from json import JSONDecodeError, loads
from logging import Logger, getLogger
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from cardserver.protocols import TableId
from cardserver.remembering import RECORD_VERSION, Kept, RoomRecord, TableRecord
from cardtable.records.naming import JOURNAL_FILE, ORIGIN_FILE, ROOM_FILE
from cardtable.records.writing import ENCODING, NEWLINE

LOGGER: Final[Logger] = getLogger("cardtable")
NO_LINES: Final[str] = ""


class RecordUnread(ValueError):
    """Raised when what stands in one directory reads as no record of a table this run opens."""


def reads_as_json(line: str) -> bool:
    """Whether one line of a journal stands as the written commit a record is read back through."""
    try:
        loads(line)
    except JSONDecodeError:
        return False

    return True


def whole_lines(text: str, table: TableId) -> tuple[str, ...]:
    """Every commit written down whole, leaving behind a last line a run was cut off in the middle of.

    A line counts once the newline after it is down, which is the one rule a reader and a writer both keep:
    the record is read to where the last newline stands and the next line is laid there, so the two agree on
    where the record ends however a run came to end. A line is laid after the lines already down and the
    record is read from the front, so whatever a run had finished writing when it ended is a record in itself.

    Raises:
        RecordUnread: when a line other than the last reads as no commit, which is a record torn where the way
            it is written leaves it whole.
    """
    written = text.split(NEWLINE)
    unfinished = written.pop()
    if unfinished:
        LOGGER.info("The last commit written down of table %r was cut short, and it is read without it", table)

    lines = [line for line in written if line]
    for number, line in enumerate(lines):
        if not reads_as_json(line):
            raise RecordUnread(f"Commit {number} of table {table!r} reads as no commit")

    return tuple(lines)


def a_room(directory: Path) -> RoomRecord:
    """The room written down in one directory, as the record it states itself to be.

    Raises:
        RecordUnread: when nothing stands there to read it from, when what stands there reads as no room, or
            when it was written in a shape this run reads records of no longer.
    """
    try:
        room = RoomRecord.model_validate_json((directory / ROOM_FILE).read_text(encoding=ENCODING))
    except (OSError, ValidationError) as unread:
        raise RecordUnread(f"The room in {directory.name!r} reads as no room: {unread}") from unread

    if room.version != RECORD_VERSION:
        raise RecordUnread(
            f"The room in {directory.name!r} was written down at version {room.version}, "
            f"and this run reads records written at version {RECORD_VERSION}"
        )

    return room


def a_table(directory: Path, table: TableId) -> TableRecord | None:
    """The table one directory holds the record of, and none where the room standing there is still settling.

    The origin is what a deal lays down first, so a directory holding one holds a table that was dealt and the
    lines beside it are however far that table had got.

    Raises:
        RecordUnread: when the origin a journal was opened at is unreadable, or when the lines beside it are
            torn somewhere other than at the end.
    """
    origin = directory / ORIGIN_FILE
    if not origin.is_file():
        return None

    journal = directory / JOURNAL_FILE
    try:
        opened = origin.read_text(encoding=ENCODING)
        lines = journal.read_text(encoding=ENCODING) if journal.is_file() else NO_LINES
    except OSError as unread:
        raise RecordUnread(f"The table in {directory.name!r} reads as no table: {unread}") from unread

    return TableRecord(origin=opened, commits=whole_lines(lines, table))


def a_kept(directory: Path) -> Kept:
    """Everything one directory of the store holds, in the shape a run gathers its lobby back from.

    When the record was last written is read off the room, since the room is written down at every change a
    company makes and at the deal besides, which is every moment a table is anything but still.

    Raises:
        RecordUnread: when what stands there reads as no record of a table this run opens.
    """
    room = a_room(directory)
    return Kept(
        room=room,
        table=a_table(directory, room.table),
        updated=(directory / ROOM_FILE).stat().st_mtime,
    )
