from collections.abc import Callable
from typing import Final

from cardserver.codes import a_drawn_code
from cardserver.creation import Creation
from cardserver.errors import NoCreation, TablesFull
from cardserver.gathering.gathering import Gathering
from cardserver.gathering.gatherings import Gatherings
from cardserver.oversight.lobby.setting import NO_LIMIT, LobbySetting
from cardserver.oversight.lobby.view import LobbyView
from cardserver.oversight.policy import AdminPolicy
from cardserver.oversight.posting import Posting
from cardserver.oversight.table_card import TableCard
from cardserver.protocols.table import TableId
from cardserver.registry import TableRegistry
from cardserver.schemas.admitted import Admitted
from cardserver.schemas.founding import Founding
from cardserver.sessions.in_service import InService

OVERSEER: Final[str] = ""
GATHERING_PHASE: Final[str] = "gathering"
PLAYING_PHASE: Final[str] = "playing"
NOTHING_ABIDES: Final[None] = None


class Oversight:
    """The overseer's view of the whole lobby, and the terms every table here is gathered and cleared under.

    This is where the two halves of the lobby are read as one — the tables still gathering and the tables in
    play — and where a run's own rules on them live: how many may stand at once, who may open one, how a fresh
    one is governed, and how long an empty one lingers before it is cleared. It carries the policy that tells
    the overseer apart as well, so the panel behind it answers to that alone and a seat reaches none of it.

    The governance a table opens under is settled here once and handed to every table gathered through it, which
    is the single place a run says whether its tables start democratic; a host toggles their own from there.

    A run that gathers a table of its own names it here as the one that abides: it is the address the run
    announced, so it stands for as long as the run does while every room a company opens falls due on the clock.
    """

    def __init__(
        self,
        gatherings: Gatherings,
        registry: TableRegistry,
        admin: AdminPolicy,
        clock: Callable[[], float],
        *,
        democratic: bool,
        creation: Creation,
        stale_seconds: float,
        idle_seconds: float,
        capacity: int = NO_LIMIT,
        abiding: TableId | None = NOTHING_ABIDES,
    ) -> None:
        self._gatherings = gatherings
        self._registry = registry
        self._admin = admin
        self._clock = clock
        self._democratic = democratic
        self._creation = creation
        self._capacity = capacity
        self._stale_seconds = stale_seconds
        self._idle_seconds = idle_seconds
        self._abiding = abiding

    def confirm(self, credential: str | None) -> None:
        """Confirm a request carries the overseer's own credential, which the panel is answered behind.

        Raises:
            Unauthorized: when the credential is not the one this host oversees under.
        """
        self._admin.confirm(credential)

    def census(self) -> int:
        """How many tables stand at once, gathering and in play alike, which a cap is counted against."""
        return self._gatherings.living() + self._registry.serving()

    def found(self, founding: Founding) -> Admitted:
        """Gather a table for the guest founding it, where this host lets a guest gather one and holds room.

        Raises:
            NoCreation: when this host opens tables from its panel alone just now.
            TablesFull: when this host already holds as many tables as it gathers at once.
            TableTaken: when a table of that name is already gathering.
            GameValidationError: when the choice the table opens on names a game offered nowhere.
        """
        if not self._creation.open_to_guests:
            raise NoCreation()

        self._confirm_room()
        return self._gatherings.create(founding, democratic=self._democratic)

    def post(self, posting: Posting) -> TableCard:
        """Gather a table the overseer opens on the company's behalf, holding no seat at it themselves.

        Raises:
            TablesFull: when this host already holds as many tables as it gathers at once.
            TableTaken: when a table of that name is already gathering.
            GameValidationError: when the choice the table opens on names a game offered nowhere.
        """
        self._confirm_room()
        gathering = self._gatherings.open(
            posting.table,
            a_drawn_code(),
            posting.choice,
            democratic=self._democratic,
        )
        return self._gathering_card(posting.table, gathering, self._clock())

    def lobby(self) -> LobbyView:
        """The whole lobby as the overseer reads it, under the terms it is held on."""
        return LobbyView(
            tables=self._cards(),
            census=self.census(),
            capacity=self._capacity,
            creation=self._creation,
        )

    def adjust(self, setting: LobbySetting) -> LobbyView:
        """Settle the terms the lobby is held under, a field at a time, which the overseer alone may do."""
        if setting.capacity is not None:
            self._capacity = setting.capacity

        if setting.creation is not None:
            self._creation = setting.creation

        return self.lobby()

    async def close(self, table: TableId, reason: str | None) -> None:
        """Break one table up whether it is gathering or in play, which the overseer may do over any company.

        Raises:
            UnknownTable: when this host holds no table of that name.
        """
        if table in dict(self._registry.sessions()):
            await self._retire(table, reason)
            return

        self._gatherings.break_up(table, reason)

    async def reap(self) -> tuple[TableId, ...]:
        """Clear away every table nobody is at that has sat too long, and answer with the ones cleared.

        A gathering nobody holds a stream on and a game nobody is at both come due on the clock, so the lobby a
        run leaves behind it is the lobby a run keeps: a room a company walked out of frees the name it stood
        under and the room a founder opened and forgot frees the one it took.

        The table this run gathers under its own name is left where it stands, since its address is the one the
        run handed out and a lobby that stands empty for an afternoon is still the lobby that address names.
        """
        now = self._clock()
        cleared: list[TableId] = []
        for table in self._gatherings.stale(self._stale_seconds, now):
            if table == self._abiding:
                continue

            self._gatherings.drop(table)
            cleared.append(table)

        for table in self._registry.idle(self._idle_seconds, now):
            await self._retire(table, None)
            cleared.append(table)

        return tuple(cleared)

    async def _retire(self, table: TableId, reason: str | None) -> None:
        """Break one table in play up and clear the room it was played through, which end together.

        A dealt room is the identity of the table it became, so it stands for exactly as long as that table and
        goes when it goes: what frees a name is the pair of them, and a room left behind would hold the name
        against every company that came after.
        """
        await self._registry.dismiss(table, reason)
        self._gatherings.drop(table)

    def _confirm_room(self) -> None:
        """Confirm this host holds room for another table.

        Raises:
            TablesFull: when as many tables as it gathers at once already stand.
        """
        if self._capacity != NO_LIMIT and self.census() >= self._capacity:
            raise TablesFull(self._capacity)

    def _cards(self) -> tuple[TableCard, ...]:
        """Every table this host holds as a card, the tables gathering ahead of the tables in play.

        A dealt gathering is a husk its company has left for the table it became, so it is read nowhere here:
        the gathering it was reads as a table in play, under the session that carries it now.
        """
        now = self._clock()
        gathered = tuple(
            self._gathering_card(table, gathering, now)
            for table, gathering in self._gatherings.tables()
            if not gathering.dealt
        )
        played = tuple(self._session_card(table, session, now) for table, session in self._registry.sessions())
        return gathered + played

    @staticmethod
    def _gathering_card(
        table: TableId,
        gathering: Gathering,
        now: float,
    ) -> TableCard:
        """One gathering as a card, which reads the code it admits on and the company holding it."""
        view = gathering.view(OVERSEER)
        return TableCard(
            table=table,
            phase=GATHERING_PHASE,
            idle=now - gathering.touched,
            seats=view.choice.players,
            present=gathering.present,
            host=gathering.host,
            code=view.code,
            democratic=gathering.democratic,
            closed=gathering.closed,
        )

    @staticmethod
    def _session_card(
        table: TableId,
        session: InService,
        now: float,
    ) -> TableCard:
        """One table in play as a card, which reads its size and how long it has stood without a commit."""
        return TableCard(
            table=table,
            phase=PLAYING_PHASE,
            idle=now - session.touched,
            seats=session.players,
            closed=session.closed,
        )
