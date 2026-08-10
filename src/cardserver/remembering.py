from hashlib import sha256
from typing import Final, Generic, Protocol

from cardserver.naming.seated import Seated
from cardserver.protocols.table import TableId
from cardserver.schemas.choice import Choice
from cardwork.models.base import BaseFrozen
from cardwork.presentation.tint import Tint
from cardwork.states.state import StateT
from cardwork.transactions.transaction import Transaction

RECORD_VERSION: Final[int] = 1
UNKEYED: Final[None] = None


def digest_of(token: str) -> str:
    """The mark a token is written down under, which a room reads its guest back by and hands out to nobody."""
    return sha256(token.encode()).hexdigest()


class Written(BaseFrozen, Generic[StateT]):
    """One commit as a record's own line: the key a client landed it under, and everything it changed.

    The key travels beside the commit because it is what a retry is answered by. A table read back from its
    record knows again which attempts it has already applied, so the request a flaky network prompts twice
    lands once across a restart as it does within a run. A commit the rules owed themselves carries none,
    since a key names a client's own attempt.
    """

    key: str | None
    transaction: Transaction[StateT]


class RoomRecord(BaseFrozen):
    """One room as a record holds it: who arrived, where they sit, and what the company settled to play.

    This is the whole of a gathering that outlives the run it was gathered in, and it is the header of the
    table that room became besides: a token holds its seat through the room it was minted at, so reading the
    room back is what hands a company the game they were at.

    Tokens are written down as digests of themselves. What a guest speaks through is read by lookup alone, so
    a digest answers every question a room asks of a token while what lies on disk admits nobody.

    The name the room gathers under travels inside the record, since a store is free to name what it writes
    however it keeps names safe. The seating travels with it too: that is what the plaques of a dealt table
    carry, and the deal is the moment it is settled.

    The version states the shape a record was written in. Every field here is declared and nothing else is
    admitted, so a build whose models have moved on reads a record of the version it wrote and leaves the
    rest to whoever wrote them.
    """

    table: TableId
    code: str
    choice: Choice
    host: str | None
    democratic: bool
    seats: dict[str, int | None]
    tints: dict[str, Tint]
    tokens: dict[str, str]
    ready: dict[str, bool]
    seated: dict[int, Seated]
    revision: int
    dealt: bool
    closed: bool
    reason: str | None
    version: int = RECORD_VERSION


class TableRecord(BaseFrozen):
    """The record kept of a table in service: the origin it opens at, and every commit landed on it since.

    Both halves cross this seam as text. A journal is written for the cursor one game declares while this
    adapter is written for no game in particular, so the lines travel whole and are read as a journal by
    whatever holds the rules that wrote them.
    """

    origin: str
    commits: tuple[str, ...]


class Kept(BaseFrozen):
    """One table as a run reads it back: the room it gathered in, the table it became, and when it last moved.

    A record holding a room alone is a company still settling what to play. A record holding a table besides
    is a game in service, whatever the room says of itself: the journal is opened before the room is written
    down dealt, so the journal is the mark the deal leaves.

    The reading is the store's own, taken as the record was last written, and a run reads it to say which
    records have stood long enough to collect.
    """

    room: RoomRecord
    table: TableRecord | None
    updated: float


class Remembering(Protocol):
    """Where a room and a table are written down, so a company is handed back the game they were at.

    The port lives with the consumer that needs it: a lobby knows when a room changes and a table knows when a
    commit lands, and each says so here. Where the words go is the host's own business, the same shape and for
    the same reason as `Opening`.

    A room is written whole and a table is written a line at a time, because that is what each of them is. A
    room is a state a company settles and settles again, small enough to hand over entire. A table is a record
    that only grows, so every commit is one line more and the lines already down stand as they were.
    """

    def remember_room(self, record: RoomRecord) -> None:
        """Write one room down as it stands, which is what a run reads a gathering back from."""

    def open_journal(self, table: TableId, origin: str) -> None:
        """Open the record of one table at the origin its journal stands on, which a deal does."""

    def append(self, table: TableId, line: str) -> None:
        """Lay one commit into the record of a table, which every commit that lands on it does."""

    def forget(self, table: TableId) -> None:
        """Drop everything written down of one table, which clearing it away and breaking it up both do."""

    def set_aside(self, table: TableId) -> None:
        """Set the record of one table aside as one nothing here reads, leaving it for whoever comes to look.

        A record is read by the run that finds it, and a run whose rules have moved on since it was written
        finds records it makes nothing of. Setting one aside is what lets the tables beside it open: the run
        says so of the one record and gathers the rest.
        """

    def kept(self) -> tuple[Kept, ...]:
        """Everything written down here, which is what a run gathers its lobby from as it starts."""


class Forgetful:
    """A host that writes nothing down, which is what a run keeping its tables for its own lifetime holds.

    Every writer says what it does whether or not anyone is listening, so this is what stands where a run
    gathers tables that live as long as it does, and the writers stay free of a question about it.
    """

    def remember_room(self, record: RoomRecord) -> None:
        """Hear the room out and let it stand for the run alone."""

    def open_journal(self, table: TableId, origin: str) -> None:
        """Hear the deal out and let the table stand for the run alone."""

    def append(self, table: TableId, line: str) -> None:
        """Hear the commit out and let it stand for the run alone."""

    def forget(self, table: TableId) -> None:
        """Hear the table cleared away, which leaves as much written down as it found."""

    def set_aside(self, table: TableId) -> None:
        """Hear the record set aside, which is a word about a record a run of this kind holds none of."""

    def kept(self) -> tuple[Kept, ...]:
        """The tables a run of this kind starts with, which is none of them."""
        return ()


FORGETFUL: Final[Forgetful] = Forgetful()
