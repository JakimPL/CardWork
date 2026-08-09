from collections.abc import Mapping
from typing import Protocol

from cardserver.naming.seated import Seated
from cardserver.protocols.table import TableId
from cardserver.schemas.choice import Choice


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
