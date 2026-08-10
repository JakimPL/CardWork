from pathlib import Path
from shutil import rmtree
from typing import TextIO

from cardserver.protocols import TableId
from cardserver.remembering import FORGETFUL, Kept, Remembering, RoomRecord
from cardtable.paths import RECORDS
from cardtable.records.holding import LOCK_PATIENCE, a_held_store
from cardtable.records.naming import (
    JOURNAL_FILE,
    LOCK_FILE,
    ORIGIN_FILE,
    ROOM_FILE,
    SET_ASIDE,
    a_directory_name,
)
from cardtable.records.reading import LOGGER, RecordUnread, a_kept
from cardtable.records.writing import a_made_directory, an_open_journal, written_whole
from cardwork.models.base import BaseFrozen


class Records(BaseFrozen):
    """What one run does with the tables it holds: whether it writes them down, and where it writes them.

    A run that writes its tables down hands a company back the game they were at when the process serving them
    ended, which is what a deployment started and stopped around its own traffic asks for. A run that keeps
    nothing holds its tables for as long as it runs, which is what a checkout being played with does.

    Where they go is a directory named outright, and the records directory of the checkout where a file names
    none. A deployment that has changed the rules under its company starts clean by clearing that directory.
    """

    kept: bool
    directory: Path | None


class Ledger:
    """The store one run writes its tables to, a directory to each of them, held for this run alone.

    A room is laid down whole at every change it goes through and a table a line at a time, because that is
    what each of them is: a room is a state a company settles and settles again, small enough to hand over
    entire, and a table is a record that only grows. A room lands under its own name in one step, so a reader
    finds the room it was before or the room it became. A line lands after the lines already down and reaches
    the file system as it is written, so a sequence a client has been told about is on disk before it hears.

    The store is held for the run, so one run writes it and a host started over another waits for it. Letting
    go is what a run does as it ends, whether it says so or the process ending says it.
    """

    def __init__(self, store: Path, patience: float) -> None:
        self._store = a_made_directory(store)
        self._holding = a_held_store(store / LOCK_FILE, patience)
        self._journals: dict[TableId, TextIO] = {}

    def remember_room(self, record: RoomRecord) -> None:
        """Write one room down as it stands, over whatever stood written before."""
        written_whole(self._directory(record.table) / ROOM_FILE, record.model_dump_json())

    def open_journal(self, table: TableId, origin: str) -> None:
        """Open the record of one table at the origin its journal stands on, which a deal does."""
        directory = self._directory(table)
        written_whole(directory / ORIGIN_FILE, origin)
        self._close(table)
        self._journals[table] = an_open_journal(directory / JOURNAL_FILE, afresh=True)

    def append(self, table: TableId, line: str) -> None:
        """Lay one commit into the record of a table, after every commit already down.

        A table read back from a record is one this run opened no journal of, so the first line it goes on to
        write opens the journal at the end of the lines that were already there.
        """
        writing = self._journals.get(table)
        if writing is None:
            writing = an_open_journal(self._directory(table) / JOURNAL_FILE, afresh=False)
            self._journals[table] = writing

        writing.write(f"{line}\n")
        writing.flush()

    def forget(self, table: TableId) -> None:
        """Drop everything written down of one table, which clearing it away and breaking it up both do."""
        self._close(table)
        directory = self._store / a_directory_name(table)
        if directory.is_dir():
            rmtree(directory)

    def set_aside(self, table: TableId) -> None:
        """Set the record of one table aside as one nothing here reads, leaving it for whoever comes to look."""
        self._close(table)
        self._aside(self._store / a_directory_name(table))

    def kept(self) -> tuple[Kept, ...]:
        """Everything written down here, with a record this run makes nothing of set aside and passed over.

        Serving the tables a run does read beats answering for none of them over one record left by a build
        whose models have moved on, so a record that reads as nothing stops at the table it belongs to and
        stays on disk under a name this run passes over.
        """
        return tuple(filter(None, (self._read(directory) for directory in self._directories())))

    def close(self) -> None:
        """Let go of the store, closing the journals held open and the hold this run has it by.

        A run holds its store for as long as it runs, so the process ending is what usually does this. Saying
        it outright is what lets a second run over the same directory pick up where the first left off.
        """
        for table in tuple(self._journals):
            self._close(table)

        self._holding.close()

    def _read(self, directory: Path) -> Kept | None:
        """What one directory holds, and nothing where it holds a record this run makes nothing of."""
        try:
            return a_kept(directory)
        except RecordUnread as unread:
            LOGGER.warning("The record in %r is set aside: %s", directory.name, unread)
            self._aside(directory)
            return None

    def _directories(self) -> tuple[Path, ...]:
        """Every directory of the store a record is looked for in, in the order their names stand in."""
        return tuple(
            directory
            for directory in sorted(self._store.iterdir())
            if directory.is_dir() and not directory.name.endswith(SET_ASIDE)
        )

    def _directory(self, table: TableId) -> Path:
        """The directory one table is written down in, made where this is the first word written of it."""
        return a_made_directory(self._store / a_directory_name(table))

    def _aside(self, directory: Path) -> None:
        """Move one directory to the name a record this run passes over stands under."""
        if not directory.is_dir():
            return

        aside = directory.with_name(f"{directory.name}{SET_ASIDE}")
        if aside.is_dir():
            rmtree(aside)

        directory.replace(aside)

    def _close(self, table: TableId) -> None:
        """Let go of the journal of one table, where this run holds it open."""
        writing = self._journals.pop(table, None)
        if writing is not None:
            writing.close()


def a_ledger(records: Records) -> Remembering:
    """Where this run writes its tables down: a store on disk, or nowhere at all where a run keeps nothing.

    Raises:
        StoreTaken: when another run still holds the store this one was pointed at, which is a host started
            over one that has yet to let go of it.
    """
    if not records.kept:
        return FORGETFUL

    return Ledger(RECORDS if records.directory is None else records.directory, LOCK_PATIENCE)
