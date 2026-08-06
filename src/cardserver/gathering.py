from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from secrets import token_urlsafe
from typing import Final, Protocol

from cardserver.codes import admits
from cardserver.errors import (
    GatheringOver,
    NameTaken,
    NoSay,
    NoSuchSeat,
    SeatsEmpty,
    SeatTaken,
    StaleGathering,
    TintTaken,
    Unadmitted,
    Unauthenticated,
    UnknownTable,
)
from cardserver.naming import Seated
from cardserver.protocol import TableId
from cardserver.schemas import (
    Admitted,
    Arriving,
    Choice,
    Choosing,
    Claiming,
    Dealing,
    GatheringView,
    Guest,
    Offering,
    Tinting,
)
from cardwork.exceptions import GameValidationError
from cardwork.presentation.tint import Tint

TOKEN_BYTES: Final[int] = 32
TINTS: Final[tuple[Tint, ...]] = tuple(Tint)
COMPANY_MOST: Final[int] = len(TINTS)
WRONG_CODES_ALLOWED: Final[int] = 10
TURNSTILE_WINDOW: Final[float] = 60.0
FIRST_REVISION: Final[int] = 0
STANDING: Final[None] = None


class Turnstile:
    """How many wrong codes one caller may offer before a gathering stops listening to it.

    Six ranks name some millions of hands, which is a number a program reaches and a person does not, so what
    guards a code is the rate rather than the length. Every refusal is remembered against the address it came
    from for as long as the window runs, and an address past its allowance is turned away before the code it
    offers is read at all.

    The address is the one the connection carries, so callers reaching the server through one proxy are counted
    as one caller. That is the honest reading of what a server knows of where a request came from.
    """

    def __init__(
        self,
        allowed: int,
        window: float,
        clock: Callable[[], float],
    ) -> None:
        self._allowed = allowed
        self._window = window
        self._clock = clock
        self._refusals: dict[str, tuple[float, ...]] = {}

    @classmethod
    def watching(cls, clock: Callable[[], float]) -> Turnstile:
        """A turnstile at the allowance a gathering keeps, reading the time off one clock."""
        return cls(WRONG_CODES_ALLOWED, TURNSTILE_WINDOW, clock)

    def confirm(self, caller: str) -> None:
        """Confirm this caller may offer a code.

        Raises:
            Unadmitted: when the caller has offered more wrong codes than the window allows.
        """
        if len(self._recent(caller)) >= self._allowed:
            raise Unadmitted("Too many wrong codes came from this address, so wait a moment and offer it again")

    def refused(self, caller: str) -> None:
        """Remember one wrong code against the caller that offered it."""
        self._refusals[caller] = (*self._recent(caller), self._clock())

    def _recent(self, caller: str) -> tuple[float, ...]:
        """The refusals of one caller still inside the window, which is what an allowance counts."""
        since = self._clock() - self._window
        return tuple(at for at in self._refusals.get(caller, ()) if at > since)


class Opening(Protocol):
    """How a settled choice becomes a table in service, which is the host's own business.

    A gathering settles what is played and who sits where while holding the name of no game, so turning that
    into a dealt table falls to whatever holds the rules. This is the whole of what a gathering asks of it.
    """

    def open(
        self,
        table: TableId,
        choice: Choice,
        seated: Mapping[int, Seated],
    ) -> None:
        """Deal the table one gathering settled on and put it into service under that name.

        Args:
            table: the name the table is served under, which is the one its gathering stands for.
            choice: what the company settled to play.
            seated: the name and tint each seat is read by, which the plaques of the table's layout carry.

        Raises:
            GameValidationError: when the rules refuse the table or the deck the choice asks for.
        """


class Gathering:
    """One table before it is dealt: who is at it, where they sit, and what they have settled to play.

    A gathering stands in a table's place until the cards are dealt, and it is the whole of identity at this
    server: a guest arrives on the code, is minted a token, and every command they send afterwards reads back
    to the name they arrived under. The seating outlives the gathering, since the token that took a seat is the
    one that goes on to play it.

    Every change a gathering goes through happens between two awaits, so it needs no lock at all: what a table
    serialises is its commits, and a gathering commits nothing. `revision` counts the changes and only grows,
    which is what a command quotes to say where it was built and what a stream waits on to learn there is more.
    """

    def __init__(
        self,
        table: TableId,
        code: str,
        choice: Choice,
        offerings: tuple[Offering, ...],
        opening: Opening,
    ) -> None:
        self._table = table
        self._code = code
        self._offerings = offerings
        self._opening = opening
        self._seats: dict[str, int | None] = {}
        self._tints: dict[str, Tint] = {}
        self._tokens: dict[str, str] = {}
        self._watching: dict[str, int] = {}
        self._revision = FIRST_REVISION
        self._changed = asyncio.Event()
        self._dealt = False
        self._choice = self._offered(choice)

    @property
    def revision(self) -> int:
        """How many changes the gathering has been through, which a command quotes as the one it was built on."""
        return self._revision

    @property
    def dealt(self) -> bool:
        """Whether the table this gathering settled has been dealt, which is what ends the gathering."""
        return self._dealt

    def admits(self, offered: str) -> bool:
        """Whether what someone offered reads as this gathering's own code."""
        return admits(self._code, offered)

    def admit(self, name: str) -> str:
        """Take one guest into the company under a name and the first free tint, and mint their token.

        The code is read before this rather than inside it, since a wrong one is what a turnstile counts. A
        company is gathered up to the tints that tell it apart, so the guest arriving is handed one and may take
        another for as long as the room stands.

        Raises:
            GatheringOver: once the table has been dealt.
            Unadmitted: when every tint is held, which is a company as large as a gathering takes.
            NameTaken: when the name is already read at this table.
        """
        self._confirm_gathering()
        tint = self._a_free_tint()
        if name in self._seats:
            raise NameTaken(name)

        token = token_urlsafe(TOKEN_BYTES)
        self._seats[name] = STANDING
        self._tints[name] = tint
        self._tokens[token] = name
        self._publish()
        return token

    def guest(self, token: str) -> str:
        """The guest a token speaks for.

        Raises:
            Unauthenticated: when the token was minted at no gathering of this table.
        """
        name = self._tokens.get(token)
        if name is None:
            raise Unauthenticated(self._table)

        return name

    def seat(self, token: str) -> int | None:
        """The seat a token holds, and None for a guest standing at none.

        Raises:
            Unauthenticated: when the token was minted at no gathering of this table.
        """
        return self._seats[self.guest(token)]

    def seat_of(self, guest: str) -> int | None:
        """The seat one guest of the company holds, and None while they are standing."""
        return self._seats.get(guest)

    def view(self, guest: str) -> GatheringView:
        """The gathering as one of its guests reads it."""
        return GatheringView(
            table=self._table,
            code=self._code,
            company=self._company(),
            choice=self._choice,
            mine=guest,
            revision=self._revision,
            dealt=self._dealt,
        )

    def attends(self, guest: str) -> None:
        """Read a guest as present, which is what holding a stream on the gathering says of them."""
        self._watching[guest] = self._watching.get(guest, 0) + 1
        self._publish()

    def leaves(self, guest: str) -> None:
        """Read a guest as gone once the last stream they were holding has been hung up."""
        self._watching[guest] = max(self._watching.get(guest, 0) - 1, 0)
        self._publish()

    def claim(self, guest: str, seat: int | None, base_revision: int) -> None:
        """Seat one guest at the table, or stand them up where they name no seat.

        Raises:
            GatheringOver: once the table has been dealt.
            StaleGathering: when the gathering has moved past the revision this was built on.
            NoSuchSeat: when the seat stands outside the table the gathering settled on.
            SeatTaken: when another guest of the company holds it.
        """
        self._confirm_gathering()
        self._confirm_revision(base_revision)
        if seat is not None:
            self._confirm_seat(guest, seat)

        self._seats[guest] = seat
        self._publish()

    def tint(self, guest: str, chosen: Tint, base_revision: int) -> None:
        """Give one guest the tint they asked for, which the company then tells them apart by.

        A tint is a guest's own whether they are sitting or standing, so this asks nothing of the seating: what
        it asks is that no one else at the table is already read by it.

        Raises:
            GatheringOver: once the table has been dealt.
            StaleGathering: when the gathering has moved past the revision this was built on.
            TintTaken: when another guest of the company holds it.
        """
        self._confirm_gathering()
        self._confirm_revision(base_revision)
        self._confirm_tint(guest, chosen)
        self._tints[guest] = chosen
        self._publish()

    def choose(self, choice: Choice, base_revision: int) -> None:
        """Settle what the table plays, standing up whoever sat past the seats it comes to hold.

        Raises:
            GatheringOver: once the table has been dealt.
            StaleGathering: when the gathering has moved past the revision this was built on.
            GameValidationError: when the choice names a game the host offers nowhere, a table that game
                seats nowhere, or a count of decks it is dealt from nowhere.
        """
        self._confirm_gathering()
        self._confirm_revision(base_revision)
        self._choice = self._offered(choice)
        self._stand_up_past(choice.players)
        self._publish()

    def deal(self, base_revision: int) -> None:
        """Deal the table the company settled on, which puts it into service and ends the gathering.

        Raises:
            GatheringOver: once the table has been dealt.
            StaleGathering: when the gathering has moved past the revision this was built on.
            SeatsEmpty: when a seat of the table stands empty.
            GameValidationError: when the rules refuse the table the choice asks for.
        """
        self._confirm_gathering()
        self._confirm_revision(base_revision)
        seated = self._seated()
        self._confirm_seated(seated)
        self._opening.open(self._table, self._choice, seated)
        self._dealt = True
        self._publish()

    async def since(self, cursor: int, guest: str) -> GatheringView:
        """The gathering as one guest reads it once it stands at `cursor`, waiting while it stands short of it.

        A gathering changes without awaiting anything, so the event a waiter takes hold of is the one the next
        change will set and nothing lands between reading the revision and waiting on it.
        """
        while self._revision < cursor:
            await self._changed.wait()

        return self.view(guest)

    def _publish(self) -> None:
        """Count the change and wake everyone watching, which is the whole of how a gathering is followed."""
        self._revision += 1
        changed, self._changed = self._changed, asyncio.Event()
        changed.set()

    def _company(self) -> tuple[Guest, ...]:
        """Everyone at the gathering, in the order they arrived."""
        return tuple(
            Guest(
                name=name,
                tint=self._tints[name],
                seat=seat,
                present=self._watching.get(name, 0) > 0,
            )
            for name, seat in self._seats.items()
        )

    def _seated(self) -> Mapping[int, Seated]:
        """The name and tint every taken seat is read by."""
        return {
            seat: Seated(name=name, tint=self._tints[name]) for name, seat in self._seats.items() if seat is not None
        }

    def _a_free_tint(self) -> Tint:
        """The first tint no guest of the company holds, which is the one an arrival is handed.

        The tints are also the room a gathering holds: a company is as large as the marks that tell it apart,
        so the arrival finding none left is the arrival there is no room for.

        Raises:
            Unadmitted: when every tint is held.
        """
        held = set(self._tints.values())
        for tint in TINTS:
            if tint not in held:
                return tint

        raise Unadmitted(f"This table gathers a company of {COMPANY_MOST}, and that many are already at it")

    def _offered(self, choice: Choice) -> Choice:
        """The choice as it stands once confirmed against what the host offers.

        Raises:
            GameValidationError: when the game is offered nowhere, or is played at no such table.
        """
        for offering in self._offerings:
            if offering.game == choice.game:
                offering.confirm(choice)
                return choice

        raise GameValidationError(f"This host offers {self._games_spoken()}, and {choice.game!r} was asked for")

    def _games_spoken(self) -> str:
        """The games on offer as a phrase, which is how a refusal states what may be played here."""
        return ", ".join(repr(offering.game) for offering in self._offerings)

    def _stand_up_past(self, players: int) -> None:
        """Stand up whoever holds a seat the table no longer has, which a smaller table leaves outside it."""
        for name, seat in self._seats.items():
            if seat is not None and seat >= players:
                self._seats[name] = STANDING

    def _confirm_gathering(self) -> None:
        """Confirm the gathering is still open to change.

        Raises:
            GatheringOver: once the table has been dealt.
        """
        if self._dealt:
            raise GatheringOver(self._table)

    def _confirm_revision(self, base_revision: int) -> None:
        """Confirm the command was built on where the gathering stands.

        Raises:
            StaleGathering: when the gathering has moved on since.
        """
        if base_revision != self._revision:
            raise StaleGathering(base_revision, self._revision)

    def _confirm_seat(self, guest: str, seat: int) -> None:
        """Confirm the seat is one of the table's own, and standing empty or already this guest's.

        Raises:
            NoSuchSeat: when the seat stands outside the table the gathering settled on.
            SeatTaken: when another guest of the company holds it.
        """
        if not 0 <= seat < self._choice.players:
            raise NoSuchSeat(seat, self._choice.players)

        for name, held in self._seats.items():
            if held == seat and name != guest:
                raise SeatTaken(seat, name)

    def _confirm_tint(self, guest: str, chosen: Tint) -> None:
        """Confirm the tint is nobody else's, which is what keeps a company telling itself apart.

        Raises:
            TintTaken: when another guest of the company holds it.
        """
        for name, held in self._tints.items():
            if held == chosen and name != guest:
                raise TintTaken(chosen.value, name)

    def _confirm_seated(self, seated: Mapping[int, Seated]) -> None:
        """Confirm every seat of the table is taken.

        Raises:
            SeatsEmpty: when a seat of the table stands empty.
        """
        empty = tuple(seat for seat in range(self._choice.players) if seat not in seated)
        if empty:
            raise SeatsEmpty(empty)


class SayPolicy(Protocol):
    """Which guests hold a say over what a table plays and when it is dealt.

    Who settles a game is a question about the company rather than about the rules, so it stands behind a call
    of its own: a table among friends asks only that a guest is sitting at it, and a deployment holding accounts
    or groups answers the same call out of what it knows of them.
    """

    def confirm(self, gathering: Gathering, guest: str) -> None:
        """Confirm this guest holds a say at this gathering.

        Raises:
            NoSay: when the guest holds none.
        """


class SeatedSay:
    """A say belongs to every guest holding a seat, which is the whole of what a friendly table asks.

    Standing at a gathering is watching it and taking a seat is joining the game, so the players of the game
    settle what is played. A guest who has taken no seat is told rather than obeyed.
    """

    def confirm(self, gathering: Gathering, guest: str) -> None:
        """Confirm the guest is sitting at the table.

        Raises:
            NoSay: when the guest holds no seat.
        """
        if gathering.seat_of(guest) is None:
            raise NoSay(guest)


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
        offerings: tuple[Offering, ...],
        say: SayPolicy,
        turnstile: Turnstile,
    ) -> None:
        self._opening = opening
        self._offerings = offerings
        self._say = say
        self._turnstile = turnstile
        self._gatherings: dict[TableId, Gathering] = {}

    @property
    def offerings(self) -> tuple[Offering, ...]:
        """Every game this host offers, which is what a gathering settles its choice among."""
        return self._offerings

    def open(self, table: TableId, code: str, choice: Choice) -> Gathering:
        """Gather one table under a name, on a code, at the choice it opens with.

        Raises:
            ValueError: when a table of that name is already gathering, which would leave the company that
                was at it holding tokens for a room that had been replaced under them.
            GameValidationError: when the opening choice names a game the host offers nowhere.
        """
        if table in self._gatherings:
            raise ValueError(f"A table named {table!r} is already gathering")

        gathering = Gathering(table, code, choice, self._offerings, self._opening)
        self._gatherings[table] = gathering
        return gathering

    def gathering(self) -> tuple[TableId, ...]:
        """The tables gathering here, which are the ones a company may still be admitted to.

        A table's name is not what admits anybody — the code is — so this is answered to a stranger: somebody
        who reached the server without the line it printed is told what there is to arrive at, and told nothing
        of who is at it.
        """
        return tuple(table for table, gathering in self._gatherings.items() if not gathering.dealt)

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
            GameValidationError: when the choice names a game or a table the host plays nowhere.
        """
        gathering = self.at(table)
        self._say.confirm(gathering, guest)
        gathering.choose(choosing.choice, choosing.base_revision)
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
