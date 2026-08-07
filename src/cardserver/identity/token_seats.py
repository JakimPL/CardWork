from collections.abc import Mapping

from cardserver.errors import Unauthenticated
from cardserver.protocols.table import TableId


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
