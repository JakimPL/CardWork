from typing import Protocol

from cardserver.protocols.table import TableId


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
