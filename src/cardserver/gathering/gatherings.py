from collections.abc import Callable

from cardserver.codes import a_drawn_code
from cardserver.errors import (
    NotTheHost,
    TableTaken,
    Unadmitted,
    Unauthenticated,
    UnknownTable,
)
from cardserver.gathering.gathering import Gathering
from cardserver.gathering.opening import Opening
from cardserver.gathering.say_policy import SayPolicy
from cardserver.gathering.turnstile import Turnstile
from cardserver.protocols.table import TableId
from cardserver.schemas.admitted import Admitted
from cardserver.schemas.arriving import Arriving
from cardserver.schemas.choice import Choice
from cardserver.schemas.choosing import Choosing
from cardserver.schemas.claiming import Claiming
from cardserver.schemas.closing import Closing
from cardserver.schemas.dealing import Dealing
from cardserver.schemas.founding import Founding
from cardserver.schemas.gathering import GatheringView
from cardserver.schemas.governing import Governing
from cardserver.schemas.offering import Offering
from cardserver.schemas.readying import Readying
from cardserver.schemas.tinting import Tinting


class Gatherings:
    """The gatherings this host holds, and the seat a credential speaks for at each of them.

    This is the server's identity policy as much as its lobby, which is what lets a table be gathered without
    accounts: a token minted at arrival holds the seat its guest has taken, holds none while they are standing,
    and belongs nowhere when it was minted at no gathering here. The endpoints a table is played at ask for the
    seat alone and are answered by that, so play is authorised by the same arrival that seated it.
    """

    def __init__(
        self,
        opening: Opening,
        *,
        offerings: tuple[Offering, ...],
        say: SayPolicy,
        turnstile: Turnstile,
        clock: Callable[[], float],
        presence_stands: float,
    ) -> None:
        self._opening = opening
        self._offerings = offerings
        self._say = say
        self._turnstile = turnstile
        self._clock = clock
        self._presence_stands = presence_stands
        self._gatherings: dict[TableId, Gathering] = {}

    @property
    def offerings(self) -> tuple[Offering, ...]:
        """Every game this host offers, which is what a gathering settles its choice among."""
        return self._offerings

    def open(
        self,
        table: TableId,
        code: str,
        choice: Choice,
        *,
        democratic: bool,
        host: str | None = None,
    ) -> Gathering:
        """Gather one table under a name, on a code, at the choice it opens with.

        Raises:
            TableTaken: when a table of that name is already gathering, which would leave the company that
                was at it holding tokens for a room that had been replaced under them.
            GameValidationError: when the opening choice names a game the host offers nowhere.
        """
        if table in self._gatherings:
            raise TableTaken(table)

        gathering = Gathering(
            table,
            code,
            choice,
            self._offerings,
            self._opening,
            clock=self._clock,
            presence_stands=self._presence_stands,
            democratic=democratic,
            host=host,
        )
        self._gatherings[table] = gathering
        return gathering

    def create(self, founding: Founding, *, democratic: bool) -> Admitted:
        """Gather a fresh table on a drawn code and seat its founder as the host, minting their token.

        Founding a table is arriving at it, so the founder is admitted the way any guest is and handed the
        token they will speak through: the code is drawn for them rather than offered, and the view answering
        carries it for them to pass on to whoever they mean to gather.

        Raises:
            TableTaken: when a table of that name is already gathering.
            GameValidationError: when the choice the table opens on names a game offered nowhere.
        """
        gathering = self.open(
            founding.table,
            a_drawn_code(),
            founding.choice,
            host=founding.name,
            democratic=democratic,
        )
        token = gathering.admit(founding.name)
        return Admitted(token=token, gathering=gathering.view(founding.name))

    def gathering(self) -> tuple[TableId, ...]:
        """The tables gathering here, which are the ones a company may still be admitted to.

        A table's name is not what admits anybody — the code is — so this is answered to a stranger: somebody
        who reached the server without the line it printed is told what there is to arrive at, and told nothing
        of who is at it.
        """
        return tuple(
            table for table, gathering in self._gatherings.items() if not gathering.dealt and not gathering.closed
        )

    def tables(self) -> tuple[tuple[TableId, Gathering], ...]:
        """Every gathering this host holds, dealt and closed alike, which is what overseeing reads the lobby by."""
        return tuple(self._gatherings.items())

    def living(self) -> int:
        """How many tables stand open to a company, which is what a cap on the lobby is counted against."""
        return sum(1 for gathering in self._gatherings.values() if not gathering.dealt and not gathering.closed)

    def stale(self, idle: float, now: float) -> tuple[TableId, ...]:
        """The tables nobody is at that have sat unchanged too long, which is what a reaper comes to clear.

        A gathering is stale once no one holds a stream on it and the clock has run past the allowance since it
        last changed, so a room a company left and a room a founder opened and never returned to both fall due.

        A room whose table has been dealt stands for as long as that table does, and is cleared away with it.
        It is the whole of identity there — a token holds its seat through the room it was minted at — and its
        company has crossed over to the table's own stream, so the two marks a room is read stale by are marks
        of a room that is over rather than of one nobody wants: it changes no further, and nobody looks at it
        again. Clearing it would leave every seat of a game still in service turned away from it.
        """
        return tuple(
            table
            for table, gathering in self._gatherings.items()
            if not gathering.dealt and gathering.present == 0 and now - gathering.touched > idle
        )

    def drop(self, table: TableId) -> None:
        """Forget one gathering, which a reaper does once it is stale and a founder does by breaking it up."""
        self._gatherings.pop(table, None)

    def at(self, table: TableId) -> Gathering:
        """The gathering of one table.

        Raises:
            UnknownTable: when this host gathers no table of that name.
        """
        gathering = self._gatherings.get(table)
        if gathering is None:
            raise UnknownTable(table)

        return gathering

    def seat(self, table: TableId, credential: str | None) -> int | None:
        """The seat a credential holds at one table, and None for a client that offered none.

        Raises:
            UnknownTable: when this host gathers no table of that name.
            Unauthenticated: when the token was minted at no gathering of this table.
        """
        if credential is None:
            return None

        return self.at(table).seat(credential)

    def guest(self, table: TableId, credential: str | None) -> str:
        """The guest a credential speaks for at one table.

        A gathering is read by the company at it, since the code admitting a guest is among the things that
        company holds: a client offering no token is turned away rather than shown the room.

        Raises:
            UnknownTable: when this host gathers no table of that name.
            Unauthenticated: when no token was offered, or when it was minted at no gathering of this table.
        """
        if credential is None:
            raise Unauthenticated(table)

        return self.at(table).guest(credential)

    def arrive(
        self,
        table: TableId,
        arriving: Arriving,
        caller: str,
    ) -> Admitted:
        """Admit one person on the code they offered, and mint the token they will speak through.

        A wrong code is counted against the address it came from, so guessing at a hand of ranks costs a caller
        its allowance rather than costing the table its privacy.

        Raises:
            UnknownTable: when this host gathers no table of that name.
            Unadmitted: when the code offered reads as another hand of ranks, when the address has offered more
                wrong codes than the window allows, or when the company is already as large as it gets.
            GatheringOver: once the table has been dealt.
            NameTaken: when the name is already read at this table.
        """
        gathering = self.at(table)
        self._turnstile.confirm(caller)
        if not gathering.admits(arriving.code):
            self._turnstile.refused(caller)
            raise Unadmitted("The code offered admits nobody at this table")

        token = gathering.admit(arriving.name)
        return Admitted(token=token, gathering=gathering.view(arriving.name))

    def claim(
        self,
        table: TableId,
        guest: str,
        claiming: Claiming,
    ) -> GatheringView:
        """Seat one guest at the table, or stand them up where they name no seat.

        Raises:
            UnknownTable: when this host gathers no table of that name.
            GatheringOver: once the table has been dealt.
            StaleGathering: when the gathering has moved past the revision this was built on.
            NoSuchSeat: when the seat stands outside the table the gathering settled on.
            SeatTaken: when another guest of the company holds it.
        """
        gathering = self.at(table)
        gathering.claim(guest, claiming.seat, claiming.base_revision)
        return gathering.view(guest)

    def tint(
        self,
        table: TableId,
        guest: str,
        tinting: Tinting,
    ) -> GatheringView:
        """Give one guest the tint they asked for, which any guest may ask for their own.

        Raises:
            UnknownTable: when this host gathers no table of that name.
            GatheringOver: once the table has been dealt.
            StaleGathering: when the gathering has moved past the revision this was built on.
            TintTaken: when another guest of the company holds it.
        """
        gathering = self.at(table)
        gathering.tint(guest, tinting.tint, tinting.base_revision)
        return gathering.view(guest)

    def choose(
        self,
        table: TableId,
        guest: str,
        choosing: Choosing,
    ) -> GatheringView:
        """Settle what the table plays, which every guest holding a say may do.

        Raises:
            UnknownTable: when this host gathers no table of that name.
            NoSay: when this guest holds no say over what the table plays.
            GatheringOver: once the table has been dealt.
            StaleGathering: when the gathering has moved past the revision this was built on.
            SeatsHeld: when a guest other than the host settles a table too small for a seat the company holds.
            GameValidationError: when the choice names a game or a table the host plays nowhere.
        """
        gathering = self.at(table)
        self._say.confirm(gathering, guest)
        gathering.choose(guest, choosing.choice, choosing.base_revision)
        return gathering.view(guest)

    def deal(
        self,
        table: TableId,
        guest: str,
        dealing: Dealing,
    ) -> GatheringView:
        """Deal the table the company settled on, which every guest holding a say may call for.

        Raises:
            UnknownTable: when this host gathers no table of that name.
            NoSay: when this guest holds no say over when the table is dealt.
            GatheringOver: once the table has been dealt.
            StaleGathering: when the gathering has moved past the revision this was built on.
            SeatsEmpty: when a seat of the table stands empty.
            GameValidationError: when the rules refuse the table the choice asks for.
        """
        gathering = self.at(table)
        self._say.confirm(gathering, guest)
        gathering.deal(dealing.base_revision)
        return gathering.view(guest)

    def ready(
        self,
        table: TableId,
        guest: str,
        readying: Readying,
    ) -> GatheringView:
        """Take one seated guest's commitment to the settings, or take it back, which any seated guest may do.

        Raises:
            UnknownTable: when this host gathers no table of that name.
            NoSay: when the guest holds no seat, since a commitment is a player's to give.
            GatheringOver: once the table has been dealt.
            TableClosed: once the gathering has been broken up.
            StaleGathering: when the gathering has moved past the revision this was built on.
        """
        gathering = self.at(table)
        gathering.ready(guest, readying.ready, readying.base_revision)
        return gathering.view(guest)

    def govern(
        self,
        table: TableId,
        guest: str,
        governing: Governing,
    ) -> GatheringView:
        """Settle how the table is governed, which its host alone may do.

        Raises:
            UnknownTable: when this host gathers no table of that name.
            NotTheHost: when the guest is not the host of the table.
            GatheringOver: once the table has been dealt.
            TableClosed: once the gathering has been broken up.
            StaleGathering: when the gathering has moved past the revision this was built on.
        """
        gathering = self.at(table)
        self._confirm_host(gathering, guest)
        gathering.govern(governing.democratic, governing.base_revision)
        return gathering.view(guest)

    def close(
        self,
        table: TableId,
        guest: str,
        closing: Closing,
    ) -> None:
        """Break a gathering up, which its host may call for, leaving the company a word on why.

        Raises:
            UnknownTable: when this host gathers no table of that name.
            NotTheHost: when the guest is not the host of the table.
        """
        gathering = self.at(table)
        self._confirm_host(gathering, guest)
        gathering.close(closing.reason)

    def break_up(self, table: TableId, reason: str | None) -> None:
        """Break a gathering up over the company's head, which overseeing does and a reaper does.

        Raises:
            UnknownTable: when this host gathers no table of that name.
        """
        self.at(table).close(reason)

    def _confirm_host(self, gathering: Gathering, guest: str) -> None:
        """Confirm the guest is the host of the table, whose say the governing of it answers to.

        Raises:
            NotTheHost: when the guest is not the host.
        """
        if guest != gathering.host:
            raise NotTheHost(guest)
