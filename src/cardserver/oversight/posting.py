from cardserver.protocols.table import TableId
from cardserver.schemas.choice import Choice
from cardwork.models.base import BaseFrozen


class Posting(BaseFrozen):
    """The overseer gathering a table on the company's behalf: the name it answers under, and what it opens on."""

    table: TableId
    choice: Choice
