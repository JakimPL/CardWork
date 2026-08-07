from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from secrets import token_urlsafe

from cardserver.codes import admits
from cardserver.errors import (
    GatheringOver,
    NameTaken,
    NoSay,
    NoSuchSeat,
    NotReady,
    SeatsEmpty,
    SeatTaken,
    StaleGathering,
    TableClosed,
    TintTaken,
    Unadmitted,
    Unauthenticated,
)
from cardserver.gathering.config import COMPANY_MOST, FIRST_REVISION, STANDING, TINTS, TOKEN_BYTES
from cardserver.gathering.opening import Opening
from cardserver.naming.seated import Seated
from cardserver.protocols.table import TableId
from cardserver.schemas.choice import Choice
from cardserver.schemas.gathering import GatheringView
from cardserver.schemas.guest import Guest
from cardserver.schemas.offering import Offering
from cardwork.exceptions import GameValidationError
from cardwork.presentation.tint import Tint


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
        *,
        clock: Callable[[], float],
        democratic: bool,
        host: str | None = None,
    ) -> None:
        self._table = table
        self._code = code
        self._offerings = offerings
        self._opening = opening
        self._clock = clock
        self._host = host
        self._democratic = democratic
        self._seats: dict[str, int | None] = {}
        self._tints: dict[str, Tint] = {}
        self._tokens: dict[str, str] = {}
        self._watching: dict[str, int] = {}
        self._ready: dict[str, bool] = {}
        self._revision = FIRST_REVISION
        self._changed = asyncio.Event()
        self._dealt = False
        self._closed = False
        self._reason: str | None = None
        self._touched = clock()
        self._choice = self._offered(choice)

    @property
    def revision(self) -> int:
        """How many changes the gathering has been through, which a command quotes as the one it was built on."""
        return self._revision

    @property
    def dealt(self) -> bool:
        """Whether the table this gathering settled has been dealt, which is what ends the gathering."""
        return self._dealt

    @property
    def closed(self) -> bool:
        """Whether the gathering was broken up before it was dealt, which ends it and carries no one on."""
        return self._closed

    @property
    def reason(self) -> str | None:
        """The word left for the company on why the gathering was broken up, and none where it stands open."""
        return self._reason

    @property
    def host(self) -> str | None:
        """The guest who gathered the table, whose say governs it while it is settled host by host."""
        return self._host

    @property
    def democratic(self) -> bool:
        """Whether every seated guest settles what is played, or the say is the host's alone."""
        return self._democratic

    @property
    def present(self) -> int:
        """How many of the company are holding a stream open, which is how many are here to read a change."""
        return sum(1 for watching in self._watching.values() if watching > 0)

    @property
    def touched(self) -> float:
        """When the gathering last changed, read off the clock it keeps, which is what a reaper counts idle."""
        return self._touched

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
            democratic=self._democratic,
            closed=self._closed,
            reason=self._reason,
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

        Who sits where is part of what a seat commits to, so a seat taken or given up takes back every
        commitment the company had made and leaves them to commit again to the table as it now stands.

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
        self._unready()
        self._publish()

    def tint(self, guest: str, chosen: Tint, base_revision: int) -> None:
        """Give one guest the tint they asked for, which the company then tells them apart by.

        A tint is a guest's own whether they are sitting or standing, so this asks nothing of the seating: what
        it asks is that no one else at the table is already read by it. A tint is no part of what is played, so
        taking one leaves every commitment where it stood.

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

        The settings are what a company commits to, so settling them anew takes back every commitment and
        leaves the company to give its word again to the table as it now stands.

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
        self._unready()
        self._publish()

    def deal(self, base_revision: int) -> None:
        """Deal the table the company settled on, which puts it into service and ends the gathering.

        Raises:
            GatheringOver: once the table has been dealt.
            TableClosed: once the gathering has been broken up.
            StaleGathering: when the gathering has moved past the revision this was built on.
            SeatsEmpty: when a seat of the table stands empty.
            NotReady: when a seated guest has yet to commit to the settings as they stand.
            GameValidationError: when the rules refuse the table the choice asks for.
        """
        self._confirm_gathering()
        self._confirm_revision(base_revision)
        seated = self._seated()
        self._confirm_seated(seated)
        self._confirm_ready()
        self._opening.open(self._table, self._choice, seated)
        self._dealt = True
        self._publish()

    def ready(self, guest: str, ready: bool, base_revision: int) -> None:
        """Take one seated guest's commitment to the settings as they stand, or take it back.

        A commitment is a seated guest's word that the choice may be dealt, so a standing guest gives none:
        watching a table is not joining the game it settles. The word stands until a setting changes under it,
        which is what a deal called for reads to know the company is of one mind about what it is dealing.

        Raises:
            GatheringOver: once the table has been dealt.
            TableClosed: once the gathering has been broken up.
            StaleGathering: when the gathering has moved past the revision this was built on.
            NoSay: when the guest holds no seat, since a commitment is a player's to give.
        """
        self._confirm_gathering()
        self._confirm_revision(base_revision)
        if self._seats.get(guest) is None:
            raise NoSay(guest)

        self._ready[guest] = ready
        self._publish()

    def govern(self, democratic: bool, base_revision: int) -> None:
        """Settle how the table is governed, which the host reads its own say over the company through.

        Raises:
            GatheringOver: once the table has been dealt.
            TableClosed: once the gathering has been broken up.
            StaleGathering: when the gathering has moved past the revision this was built on.
        """
        self._confirm_gathering()
        self._confirm_revision(base_revision)
        self._democratic = democratic
        self._publish()

    def close(self, reason: str | None) -> None:
        """Break the gathering up before it is dealt, with a word for the company on why.

        Closing is the deal's twin: it ends the gathering once and for all and wakes every stream held on it,
        which is how a company reading the room learns the room is gone rather than watching it fall silent. A
        gathering already dealt is left as it was, since its company has been carried to the table and its
        stream is closed behind them.
        """
        if self._dealt or self._closed:
            return

        self._closed = True
        self._reason = reason
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
        self._touched = self._clock()
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
                ready=self._ready.get(name, False),
                host=name == self._host,
            )
            for name, seat in self._seats.items()
        )

    def _seated(self) -> Mapping[int, Seated]:
        """The name and tint every taken seat is read by."""
        return {
            seat: Seated(
                name=name,
                tint=self._tints[name],
            )
            for name, seat in self._seats.items()
            if seat is not None
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

    def _unready(self) -> None:
        """Take back every commitment, which a change to what is played or who plays it calls for."""
        self._ready.clear()

    def _confirm_gathering(self) -> None:
        """Confirm the gathering is still open to change.

        Raises:
            GatheringOver: once the table has been dealt.
            TableClosed: once the gathering has been broken up.
        """
        if self._dealt:
            raise GatheringOver(self._table)

        if self._closed:
            raise TableClosed(self._table)

    def _confirm_ready(self) -> None:
        """Confirm every seated guest has committed to the settings as they stand.

        Raises:
            NotReady: when a seat of the table is held by a guest who has yet to commit.
        """
        waiting = tuple(name for name, seat in self._seats.items() if seat is not None and not self._ready.get(name))
        if waiting:
            raise NotReady(waiting)

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
