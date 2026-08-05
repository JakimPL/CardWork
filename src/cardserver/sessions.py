import asyncio
from typing import Generic

from cardserver.errors import JournalSealed
from cardserver.protocol import Presentation, Table, TableId
from cardwork.decks.deck import Order
from cardwork.moves.move import Move
from cardwork.presentation.layout import Layout
from cardwork.states.state import StateT
from cardwork.transactions.journal import Journal
from cardwork.views.event import EventView
from cardwork.views.position import PositionView
from cardwork.zones.zone import ZoneId


class TableSession(Generic[StateT]):
    """One table under service: the game, the single writer committing to it, and the tries it has applied.

    Every command runs inside this session's lock, which is the whole of the concurrency in the system.
    The domain call it guards runs to completion without yielding, so a reader between two commands
    finds a whole position and takes no lock to do it.

    A served table needs two things a bare game does not, and both live here: the keys of the commands
    already applied, so a client that retries a request it never saw answered lands its move once, and
    the timer holding the rules back for a moment once a round closes, which is the window a seat has to
    take a commitment back. Time is the adapter's alone to keep; the engine stays synchronous.

    A table is opened with the arrangement its interface reads it through, so the session answers for both
    halves of what a client is served: the cards its seat is entitled to, and where they lie on the screen.
    """

    def __init__(
        self,
        table_id: TableId,
        table: Table[StateT],
        presentation: Presentation,
        grace_seconds: float,
    ) -> None:
        self._table_id = table_id
        self._table = table
        self._presentation = presentation
        self._grace_seconds = grace_seconds
        self._commits = asyncio.Condition()
        self._applied: dict[str, int] = {}
        self._settlement: asyncio.Task[None] | None = None
        self._revealed = False

    @property
    def head(self) -> int:
        """How many commits the table holds, which is the sequence the next one takes."""
        return self._table.head

    @property
    def settling(self) -> bool:
        """Whether the changes the rules owe stand held back on a window just now.

        A move a seat lands opens one and starts it afresh, which is the moment every seat is given to take a
        commitment back. An arrangement opens none, so a table where the seats have only sorted their cards
        holds the rules back not at all.
        """
        return self._settlement is not None and not self._settlement.done()

    @property
    def record(self) -> Journal[StateT]:
        """Every commit the table holds, cards and all.

        Raises:
            JournalSealed: while the record stays closed, since it names every card a seat still hides.
        """
        if not self._revealed:
            raise JournalSealed(self._table_id)

        return self._table.journal

    def reveal(self) -> None:
        """Open the table's full record for analysis, which the host does once the game it holds is over."""
        self._revealed = True

    def layout(self, observer: int | None) -> Layout:
        """How this table is laid out for one observer, which is what an interface draws it from.

        A layout stands for the whole of a table's service: the zones it lays out and the gestures it admits
        come from the game's rules rather than from its position, so a client reads one as it joins and holds
        it while the cards move underneath.
        """
        return self._presentation.layout(self._table.players, observer)

    def view(self, observer: int | None) -> PositionView[StateT]:
        """The table as one observer is entitled to see it, at the sequence it stands at now."""
        return self._table.view(observer)

    def events(self, observer: int | None, since: int) -> tuple[EventView[StateT], ...]:
        """Every commit from `since` onward as one observer learns of it, in commit order."""
        return self._table.events(observer, since)

    async def submit(self, move: Move, base_seq: int, key: str) -> int:
        """Apply one command to the table and answer with the sequence it was committed at.

        A key already applied answers with the sequence it reached the first time and changes nothing,
        so the retry a flaky network prompts costs a lookup. Anything else runs the engine's own
        pipeline, and a refusal from it leaves the key unclaimed for the client to try again.

        Args:
            move: the seat's intent.
            base_seq: the sequence the client built the move on.
            key: the client's name for this attempt, which every retry of it repeats.

        Raises:
            StalePosition: when further commits have landed since `base_seq`.
            NotYourTurn: when the rules withhold the turn from this seat.
            IllegalMove: when the rules reject what the move asks for.
        """
        async with self._commits:
            applied = self._applied.get(key)
            if applied is not None:
                return applied

            transaction = self._table.submit(move, base_seq)
            self._applied[key] = transaction.seq
            self._publish()
            self._restart_grace()
            return transaction.seq

    async def arrange(self, zone: ZoneId, order: Order, seat: int, base_seq: int, key: str) -> int:
        """Lay one of a seat's own zones out and answer with the sequence the order was committed at.

        This runs under the lock and answers a repeated key as `submit` does, since an arrangement is a commit
        the record holds like any other and a retried request is to land once. The window a seat has to take a
        commitment back stands where it stood: a seat sorting a zone commits nothing for anyone to take back,
        so the rules fall due at the moment the last move left them due.

        Args:
            zone: the zone to lay out, which is one this seat arranges.
            order: the positions the zone holds, in the order they come to lie.
            seat: the seat asking, which the server reads off the credential.
            base_seq: the sequence the seat read the zone at.
            key: the client's name for this attempt, which every retry of it repeats.

        Raises:
            StalePosition: when further commits have landed since `base_seq`.
            ArrangementRefused: when the seat arranges no such zone, or when the order names any run of
                positions other than the ones that zone holds.
        """
        async with self._commits:
            applied = self._applied.get(key)
            if applied is not None:
                return applied

            transaction = self._table.arrange(zone, order, seat, base_seq)
            self._applied[key] = transaction.seq
            self._publish()
            return transaction.seq

    async def watch(self, cursor: int) -> None:
        """Wait until the table holds a commit past `cursor`, which is what wakes a stream to read it."""
        async with self._commits:
            await self._commits.wait_for(lambda: self._table.head > cursor)

    async def drain(self) -> None:
        """Wait for a settlement in hand to run, which leaves the table where the rules mean it to be."""
        while (settlement := self._settlement) is not None and not settlement.done():
            await asyncio.wait((settlement,))

    async def close(self) -> None:
        """Drop a settlement still waiting on its window, so the table ends service holding no timer."""
        settlement = self._settlement
        if settlement is not None:
            settlement.cancel()
            await asyncio.wait((settlement,))

    def _publish(self) -> None:
        """Close the table's commits to undo and wake every stream watching, with the lock in hand."""
        self._table.mark_published()
        self._commits.notify_all()

    def _restart_grace(self) -> None:
        """Start the window afresh, so each command a seat lands gives every seat its moment again."""
        if self._settlement is not None:
            self._settlement.cancel()

        self._settlement = asyncio.create_task(self._settle_after_grace())

    async def _settle_after_grace(self) -> None:
        """Hold the rules back for the window, then commit whatever they owe once it has passed.

        Waiting is what makes a take-back reach a table that a keystroke of latency would otherwise
        have closed. A window that passes over a round still in play settles nothing, since the rules
        owe nothing until the last seat has acted.
        """
        await asyncio.sleep(self._grace_seconds)
        async with self._commits:
            if self._table.settle():
                self._publish()
