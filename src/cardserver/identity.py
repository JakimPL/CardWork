from collections.abc import Mapping
from typing import Final, Protocol

from cardserver.errors import Unauthenticated, WrongSeat
from cardserver.protocol import TableId

SEAT_HEADER: Final[str] = "X-Seat-Token"


class SeatPolicy(Protocol):
    """How this deployment turns a credential into a seat, which is the one thing identity means here.

    The domain counts seats and knows nothing of accounts, sessions or tokens, so the whole of identity
    policy sits behind this call and changes without a game noticing.
    """

    def seat(self, table: TableId, credential: str | None) -> int | None:
        """The seat a credential holds at one table, and None for a client that offered none.

        Raises:
            Unauthenticated: when the credential belongs to no seat at this table.
        """


class TokenSeats:
    """Seats held by opaque tokens, listed per table when the table is opened.

    A client that offers no token watches as a spectator, and a token the table issued names the seat
    it was issued for. Anything else is turned away, which leaves watching open to anyone and a seat
    open to whoever holds its token.
    """

    def __init__(self, seats: Mapping[TableId, Mapping[str, int]]) -> None:
        self._seats = seats

    def seat(self, table: TableId, credential: str | None) -> int | None:
        """The seat this token holds at the table, and None for a spectator.

        Raises:
            Unauthenticated: when the token belongs to no seat at this table.
        """
        if credential is None:
            return None

        held = self._seats.get(table, {}).get(credential)
        if held is None:
            raise Unauthenticated(table)

        return held


def seated(observer: int | None) -> int:
    """The seat behind a command that a seat of the table alone may send.

    A command naming no seat of its own is one the credential answers for entirely, so the seat it lands for
    is read here rather than confirmed. Both commands pass through this, which is what leaves one answer for
    the client holding no seat at all.

    Raises:
        WrongSeat: when a spectator sends a command, since watching a table is done at no seat of it.
    """
    if observer is None:
        raise WrongSeat("A spectator watches the table and acts at no seat of it")

    return observer


def confirm_actor(observer: int | None, player: int) -> None:
    """Confirm the client behind a command holds the seat the move was made for.

    The engine trusts `move.player`, so the seat it names is settled here, where a credential is all
    the server knows of who is asking.

    Raises:
        WrongSeat: when a spectator submits a command, or when a seat submits one made for another.
    """
    held = seated(observer)
    if held != player:
        raise WrongSeat(f"The credential holds seat {held}, and the move was made for seat {player}")
