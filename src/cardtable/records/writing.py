import os
from pathlib import Path
from typing import Final, TextIO

ENCODING: Final[str] = "utf-8"
FILE_MODE: Final[int] = 0o600
DIRECTORY_MODE: Final[int] = 0o700
PENDING: Final[str] = ".writing"
NEWLINE: Final[str] = "\n"
LINE_END: Final[bytes] = NEWLINE.encode()


def a_made_directory(directory: Path) -> Path:
    """That directory, made where it is missing and left open to the account this run is under alone.

    The mode a directory is made with is cut down by whatever mask the account runs under, so it is stated
    again once the directory stands. That matters here in particular: a journal names every card every seat
    is holding, and the whole point of a sealed table is that it is read by the table alone.
    """
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(DIRECTORY_MODE)
    return directory


def a_held_file(path: Path) -> TextIO:
    """One file opened for as long as a run holds it, made where it is missing and open to this account alone."""
    return os.fdopen(os.open(path, os.O_CREAT | os.O_RDWR, FILE_MODE), "r+", encoding=ENCODING)


def written_whole(path: Path, body: str) -> None:
    """Lay one file down entire, so what stands at that name is the whole of a body or the whole of the last.

    The body goes to a name of its own beside it and is then moved onto the name it is read under, which is
    one step a file system takes whole. So a file a run is still writing is never read as a record, and a run
    cut off in the middle of one leaves the record that was already there standing.
    """
    pending = path.with_name(f"{path.name}{PENDING}")
    pending.unlink(missing_ok=True)
    opened = os.open(pending, os.O_CREAT | os.O_EXCL | os.O_WRONLY, FILE_MODE)
    with os.fdopen(opened, "w", encoding=ENCODING) as writing:
        writing.write(body)

    os.replace(pending, path)


def cut_back_to_a_whole_line(path: Path) -> None:
    """Cut one journal back to the last line written down whole, which is where the next line belongs.

    A line counts once the newline after it is down, so whatever stands past the last newline is a line the
    run that wrote it was cut off in the middle of. Cutting it away is what a run picking the journal up does
    first, and it is the same reading the record is taken back through: a line laid after a part-written one
    would stand in the middle of the record rather than at the end of it, where every reader after would
    make nothing of the pair and take the whole table for torn.
    """
    if not path.is_file():
        return

    written = path.read_bytes()
    whole = written.rfind(LINE_END) + 1
    if whole != len(written):
        with path.open("r+b") as handle:
            handle.truncate(whole)


def an_open_journal(path: Path, *, afresh: bool) -> TextIO:
    """The journal of one table held open for the lines to come, opened empty or opened at its end.

    A deal opens the journal of the table it deals, so that one starts empty. A table read back from a record
    opens after the last line that was written down whole, which is where the next commit belongs.
    """
    if afresh:
        opened = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, FILE_MODE)
        return os.fdopen(opened, "w", encoding=ENCODING)

    cut_back_to_a_whole_line(path)
    opened = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, FILE_MODE)
    return os.fdopen(opened, "a", encoding=ENCODING)
