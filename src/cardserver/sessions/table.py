import asyncio
from collections.abc import Callable, Mapping
from typing import Generic

from cardserver.errors import JournalSealed
from cardserver.protocols.presentation import Presentation
from cardserver.protocols.table import Table, TableId
from cardserver.remembering import UNKEYED, Remembering, Written
from cardwork.decks.deck import Order
from cardwork.moves.move import Move
from cardwork.presentation.layout import Layout
from cardwork.states.state import StateT
from cardwork.transactions.journal import Journal
from cardwork.transactions.transaction import Transaction
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
        *,
        keeping: Remembering,
        grace_seconds: float,
        clock: Callable[[], float],
    ) -> None:
        self._table_id = table_id
        self._table = table
        self._presentation = presentation
        self._keeping = keeping
        self._grace_seconds = grace_seconds
        self._clock = clock
        self._commits = asyncio.Condition()
        self._applied: dict[str, int] = {}
        self._settlement: asyncio.Task[None] | None = None
        self._revealed = False
        self._closed = False
        self._reason: str | None = None
        self._touched = clock()

    @property
    def head(self) -> int:
        """How many commits the table holds, which is the sequence the next one takes."""
        return self._table.head

    @property
    def players(self) -> int:
        """How many seats the table holds, which is the size overseeing reads a played table by."""
        return self._table.players

    @property
    def settling(self) -> bool:
        """Whether the changes the rules owe stand held back on a window just now.

        A move a seat lands opens one and starts it afresh, which is the moment every seat is given to take a
        commitment back. An arrangement opens none, so a table where the seats have only sorted their cards
        holds the rules back not at all.
        """
        return self._settlement is not None and not self._settlement.done()

    @property
    def closed(self) -> bool:
        """Whether the table has been broken up, which ends its stream the way a game over never does."""
        return self._closed

    @property
    def closing(self) -> str | None:
        """The word left for the seats on why the table was broken up, and none while it stands."""
        return self._reason

    @property
    def touched(self) -> float:
        """When the table was last committed to or last taken up, which a reaper counts a game idle by."""
        return self._touched

    def attends(self) -> None:
        """Read the table as one somebody is at, which a stream taken up on it says.

        A turn a company is still thinking about is a table nobody commits to for as long as the thinking
        takes, so what says a game is alive is a page following it rather than a move landing on it. Every
        stream says so as it is taken up, and a page picking its stream up again keeps saying it.
        """
        self._touched = self._clock()

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

    def keep(self) -> None:
        """Write the table down as it opens: the origin its record stands on, and the commits it already holds.

        A deal lands a table holding commits of its own, so opening the record and laying those into it is one
        act. They carry no key, since a key names a client's own attempt and the deal is the table's.
        """
        journal = self._table.journal
        self._keeping.open_journal(self._table_id, journal.initial.model_dump_json())
        for transaction in journal.transactions:
            self._append(transaction, UNKEYED)

    def restore(self, applied: Mapping[str, int]) -> None:
        """Take back the attempts this table has already answered, which a table read back from a record does.

        The record holds every commit the table stands on, and each line of it holds the key a client landed
        that commit under. Reading those back is what leaves a request a flaky network prompted twice answered
        the second time with the sequence it reached the first, across a restart as within a run.

        Nothing is written down here. The record already holds the table this opens at, so what a store next
        hears of it is the commit that lands after it.
        """
        self._applied = dict(applied)

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
            self._append(transaction, key)
            self._publish()
            self._restart_grace()
            return transaction.seq

    async def arrange(
        self,
        zone: ZoneId,
        order: Order,
        seat: int,
        base_seq: int,
        key: str,
    ) -> int:
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
            self._append(transaction, key)
            self._publish()
            return transaction.seq

    async def watch(self, cursor: int) -> None:
        """Wait until the table holds a commit past `cursor`, or is broken up, which wakes a stream either way.

        Waiting is for a table standing exactly where the stream does. A cursor naming a sequence beyond the
        table's own is a cursor from a table this one has never been, so it is answered at once and the stream
        reads how far the record really goes.
        """
        async with self._commits:
            await self._commits.wait_for(lambda: self._table.head != cursor or self._closed)

    async def dismiss(self, reason: str | None) -> None:
        """Break the table up, waking every stream on it so its seats learn the game is over rather than gone quiet.

        Breaking up is terminal: the flag is raised under the lock and every waiter woken, so a stream reads the
        table closed the next time it looks and carries a last word for it. The window a move left open is
        dropped as service ends, since a table nobody may commit to again owes its seats nothing to settle.
        """
        async with self._commits:
            if self._closed:
                return

            self._closed = True
            self._reason = reason
            self._touched = self._clock()
            self._commits.notify_all()

        await self.close()

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

    def _append(self, transaction: Transaction[StateT], key: str | None) -> None:
        """Lay one commit into the record kept of this table, under the key a client landed it by.

        Every commit is written down before the stream that carries it is woken, so a sequence a client has
        been told about is one the record already holds and a table read back stands where its seats left it.
        """
        self._keeping.append(self._table_id, Written(key=key, transaction=transaction).model_dump_json())

    def _publish(self) -> None:
        """Close the table's commits to undo and wake every stream watching, with the lock in hand."""
        self._table.mark_published()
        self._touched = self._clock()
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
            settled = self._table.settle()
            if settled:
                for transaction in settled:
                    self._append(transaction, UNKEYED)

                self._publish()
