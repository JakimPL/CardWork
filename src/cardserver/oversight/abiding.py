from cardserver.protocols.table import TableId
from cardserver.schemas.choice import Choice
from cardwork.models.base import BaseFrozen


class Abiding(BaseFrozen):
    """The room a run gathers under its own name, and everything it takes to gather that room again.

    A run announces one address and hands it out, so the room behind it stands for as long as the run answers
    while every room a company opened falls due on the clock. Once the table that room became has been played
    out and cleared away, this is what it is gathered back from: the name it answers under, the code it admits
    on, and the choice it opens at.

    The code travels here rather than being drawn afresh because it is the one a person was handed. A run
    reads its rooms back from what an earlier one wrote down, so the code it announces is the standing room's
    own, and the room gathered in place of a table just cleared away admits on exactly that.
    """

    table: TableId
    code: str
    choice: Choice
