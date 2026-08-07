from typing import Annotated

from pydantic import Field, field_validator

from cardserver.limits import NAME_LONGEST
from cardserver.protocols.table import TableId
from cardserver.schemas.choice import Choice
from cardwork.models.base import BaseFrozen


class Founding(BaseFrozen):
    """Gathering a new table: the name it answers under, the name its host arrives under, and what it opens on.

    The host names the table and themselves at once, since founding a table is arriving at it: the code is drawn
    for them and handed back, and the token minted seats the host the way an arrival seats any guest.
    """

    table: Annotated[TableId, Field(min_length=1, max_length=NAME_LONGEST)]
    name: Annotated[str, Field(min_length=1, max_length=NAME_LONGEST)]
    choice: Choice

    @field_validator("table", "name")
    @classmethod
    def _reads_at_a_table(cls, offered: str) -> str:
        """The name with the space around it trimmed, refused where it shows nothing, as a guest's name is.

        Raises:
            ValueError: when nothing but space was offered, or a character of it shows nothing.
        """
        read = offered.strip()
        if not read:
            raise ValueError("A name is what a table and its host are read by, and this one holds nothing but space")

        if not read.isprintable():
            raise ValueError(f"A name reads at a table, and {offered!r} holds a character that shows nothing")

        return read
