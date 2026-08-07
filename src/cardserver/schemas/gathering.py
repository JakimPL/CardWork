from typing import Annotated

from pydantic import Field

from cardserver.protocols.table import TableId
from cardserver.schemas.choice import Choice
from cardserver.schemas.guest import Guest
from cardwork.models.base import BaseFrozen


class GatheringView(BaseFrozen):
    """A gathering as one of its guests reads it: the company, what is settled, and where the gathering stands.

    `revision` counts the changes the gathering has been through, and a command quotes the one it was built on
    the way a move quotes a sequence, so two guests settling the choice at once leaves the second told rather
    than overruled. `dealt` turns true once, which is what carries every page from the gathering to the table.

    `democratic` is how the table is governed: true where every seated guest settles what is played, and false
    where the say is the host's alone. `closed` turns true when the gathering is broken up before it is dealt,
    which ends it the way the deal does but carries the company nowhere.
    """

    table: TableId
    code: str
    company: tuple[Guest, ...]
    choice: Choice
    mine: str
    revision: Annotated[int, Field(ge=0)]
    dealt: bool
    democratic: bool
    closed: bool
    reason: str | None
