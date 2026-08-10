from json import loads
from typing import Generic, Self

from cardserver.remembering import TableRecord, Written
from cardwork.models.base import BaseFrozen
from cardwork.positions.position import Position
from cardwork.states.state import StateT
from cardwork.transactions.journal import Journal


class Recorded(BaseFrozen, Generic[StateT]):
    """The record kept of one table read as the models the rules that wrote it are written for.

    A record crosses a store as text, since a store is written for no game in particular, and this is where it
    becomes a table again: a host holding the rules of the game a room settled reads the origin and every line
    beside it into the cursor those rules declare. Every field is declared and nothing else admitted, so a
    record written where the models have since moved on is refused here rather than folded into a position no
    table stands at.

    Both halves of what a table taken up needs come out of the one reading: the journal the rules are handed,
    and the sequence each client's attempt reached.
    """

    origin: Position[StateT]
    commits: tuple[Written[StateT], ...]

    @classmethod
    def read(cls, record: TableRecord) -> Self:
        """One record read as this cursor's own, which is what a run holding the rules does with the text.

        Raises:
            JSONDecodeError: when the origin the record opens at reads as nothing written down.
            ValidationError: when the origin or a line beside it was written for a cursor of another shape.
        """
        return cls.model_validate(
            {
                "origin": loads(record.origin),
                "commits": [loads(line) for line in record.commits],
            }
        )

    @property
    def journal(self) -> Journal[StateT]:
        """The record as a journal, which is what a table is handed to stand where its last commit left it."""
        return Journal(
            initial=self.origin,
            transactions=tuple(written.transaction for written in self.commits),
        )

    @property
    def applied(self) -> dict[str, int]:
        """The sequence each client's attempt reached, which is what a table read back answers a retry from."""
        return {written.key: written.transaction.seq for written in self.commits if written.key is not None}
