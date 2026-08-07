from typing import Annotated

from pydantic import Field

from cardserver.protocols.table import TableId
from cardserver.schemas.choice import Choice
from cardwork.models.base import BaseFrozen


class Posting(BaseFrozen):
    """The overseer gathering a table on the company's behalf: the name it answers under, and what it opens on."""

    table: Annotated[TableId, Field(min_length=1)]
    choice: Choice
