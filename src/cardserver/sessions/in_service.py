from typing import Protocol

from cardserver.sessions.commit import Commit
from cardwork.decks.deck import Order
from cardwork.models.base import BaseFrozen
from cardwork.moves.move import Move
from cardwork.presentation.layout import Layout
from cardwork.zones.zone import ZoneId


class InService(Protocol):
    """One table in service, answering for itself without naming the shape of the cursor its game declares.

    A game states its own state type and the projections carry it, so the sessions of two games are of two
    types and one registry holds both. Every answer carrying a cursor goes out as JSON under a schema of the
    game's own, which is what leaves the state type inside the session it was opened with: what a route asks
    of a table in service is stated here, and stated once.
    """

    @property
    def head(self) -> int:
        """How many commits the table holds, which is the sequence the next one takes."""

    @property
    def players(self) -> int:
        """How many seats the table holds, which is the size overseeing reads a played table by."""

    @property
    def settling(self) -> bool:
        """Whether the changes the rules owe stand held back on a window just now."""

    @property
    def closed(self) -> bool:
        """Whether the table has been broken up, which ends its stream the way a game over never does."""

    @property
    def closing(self) -> str | None:
        """The word left for the seats on why the table was broken up, and none while it stands."""

    @property
    def touched(self) -> float:
        """When the table was last committed to or last taken up, which a reaper counts a game idle by."""

    def attends(self) -> None:
        """Read the table as one somebody is at, which a stream taken up on it says."""

    @property
    def record(self) -> BaseFrozen:
        """Every commit the table holds, cards and all.

        Raises:
            JournalSealed: while the record stays closed.
        """

    def reveal(self) -> None:
        """Open the table's full record for analysis."""

    def layout(self, observer: int | None) -> Layout:
        """How this table is laid out for one observer."""

    def view(self, observer: int | None) -> BaseFrozen:
        """The table as one observer is entitled to see it, at the sequence it stands at now."""

    def events(self, observer: int | None, since: int) -> tuple[Commit, ...]:
        """Every commit from `since` onward as one observer learns of it, in commit order."""

    async def submit(self, move: Move, base_seq: int, key: str) -> int:
        """Apply one command to the table and answer with the sequence it was committed at."""

    async def arrange(
        self,
        zone: ZoneId,
        order: Order,
        seat: int,
        base_seq: int,
        key: str,
    ) -> int:
        """Lay one of a seat's own zones out and answer with the sequence the order was committed at."""

    async def watch(self, cursor: int) -> None:
        """Wait until the table holds a commit past `cursor`, or the table is broken up."""

    async def dismiss(self, reason: str | None) -> None:
        """Break the table up, waking every stream on it so its seats learn the game is over."""

    async def drain(self) -> None:
        """Wait for a settlement in hand to run."""

    async def close(self) -> None:
        """Drop a settlement still waiting on its window."""
