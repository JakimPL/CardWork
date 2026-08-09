from cardserver.protocols.table import TableId
from cardwork.models.base import BaseFrozen


class TableCard(BaseFrozen):
    """One table as the overseer reads it: where it stands, how large, who is at it, and how long it has idled.

    A gathering and a table in service read the same shape here, so the panel lists both in one hand: a
    gathering carries the code it admits on and the company reading it, and a table in play carries neither,
    since its company was carried to it and its cards are the seats' own.
    """

    table: TableId
    phase: str
    idle: float
    seats: int
    present: int | None = None
    host: str | None = None
    code: str | None = None
    democratic: bool | None = None
    closed: bool = False
