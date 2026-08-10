from hashlib import sha256
from re import sub
from typing import Final

from cardserver.protocols import TableId

ROOM_FILE: Final[str] = "room.json"
ORIGIN_FILE: Final[str] = "origin.json"
JOURNAL_FILE: Final[str] = "journal.ndjson"
LOCK_FILE: Final[str] = ".lock"
SET_ASIDE: Final[str] = ".broken"

SLUG_LONGEST: Final[int] = 24
DIGEST_LENGTH: Final[int] = 16
PLAINLY: Final[str] = r"[^a-z0-9]+"
UNSLUGGED: Final[str] = "table"
SEPARATOR: Final[str] = "-"


def a_slug(table: TableId) -> str:
    """The readable half of a directory's name: the table's own name in the characters a path reads plainly.

    This is for whoever comes to the store with a file manager, so it is the name they would look for and
    nothing more is asked of it. A name written in characters none of which read plainly slugs to the word a
    table is, and the half beside it is what tells that directory from every other.
    """
    read = sub(PLAINLY, SEPARATOR, table.lower()).strip(SEPARATOR)[:SLUG_LONGEST].strip(SEPARATOR)
    return read or UNSLUGGED


def a_directory_name(table: TableId) -> str:
    """The one directory a table is written down in, so a name of any shape names one place inside the store.

    The name is read for a slug and hashed for the rest, and the hash is what the directory is told apart by:
    a name is a word a company chose, and the store stands whatever they chose. Two names reading alike slug
    alike and hash apart, so each keeps its own directory.

    The name itself is written inside the room, which is where a run reads it back from. That leaves the store
    free to name what it holds however it keeps names safe, and leaves the table free to be called anything.
    """
    return f"{a_slug(table)}{SEPARATOR}{sha256(table.encode()).hexdigest()[:DIGEST_LENGTH]}"
