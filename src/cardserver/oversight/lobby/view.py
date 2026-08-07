from cardserver.oversight.creation import Creation
from cardserver.oversight.table_card import TableCard
from cardwork.models.base import BaseFrozen


class LobbyView(BaseFrozen):
    """The lobby as the overseer reads it: every table it holds, and the terms it holds them under."""

    tables: tuple[TableCard, ...]
    census: int
    capacity: int
    creation: Creation
