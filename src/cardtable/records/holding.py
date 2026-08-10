from fcntl import LOCK_EX, LOCK_NB, flock
from pathlib import Path
from time import monotonic, sleep
from typing import Final, TextIO

from cardtable.records.writing import a_held_file

LOCK_PATIENCE: Final[float] = 10.0
LOCK_RETRY: Final[float] = 0.25


class StoreTaken(RuntimeError):
    """Raised when another run holds the store this one was told to write its tables to."""

    def __init__(self, store: Path) -> None:
        super().__init__(f"Another run holds the records in {str(store)!r}, and a store is written by one run")
        self.store = store


def taken(handle: TextIO) -> bool:
    """Whether the hold on one open file was there for the taking, taking it where it was.

    The hold is asked for without waiting, so the answer comes back either way and the run stating how long
    it will wait is the one that waits.
    """
    try:
        flock(handle, LOCK_EX | LOCK_NB)
    except BlockingIOError:
        return False

    return True


def a_held_store(lock: Path, patience: float) -> TextIO:
    """Take one store for this run alone, and hand back the handle the hold lives in.

    A record is written by the run that holds the tables it is of, so one store belongs to one run: a host
    that starts while the last one is still winding down waits for it, since a graceful shutdown is a matter
    of seconds and a restart is what this is for. A run that waits out its patience runs nowhere — a table
    written down by two runs at once is a table read back by neither.

    The hold lives in the open file and lasts as long as it does, so letting go is closing it and a run that
    ends however it ends leaves the store free for the next.

    Raises:
        StoreTaken: when another run still holds the store once the patience is out.
    """
    handle = a_held_file(lock)
    deadline = monotonic() + patience
    while not taken(handle):
        if monotonic() >= deadline:
            handle.close()
            raise StoreTaken(lock.parent)

        sleep(LOCK_RETRY)

    return handle
