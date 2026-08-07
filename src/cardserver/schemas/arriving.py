from typing import Annotated, Final

from pydantic import Field, field_validator

from cardwork.models.base import BaseFrozen

NAME_LONGEST: Final[int] = 24  # TODO: move to advanced server configuration


class Arriving(BaseFrozen):
    """One person arriving at a table: the code that admits them, and the name they will be read by."""

    code: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1, max_length=NAME_LONGEST)]

    @field_validator("name")
    @classmethod
    def _a_name_reads_at_the_table(cls, offered: str) -> str:
        """The name with the space around it trimmed off, which is how the company comes to read it.

        Raises:
            ValueError: when nothing but space was offered, or when a character of it shows nothing.
        """
        read = offered.strip()
        if not read:
            raise ValueError("A name is what the company reads a guest by, and this one holds nothing but space")

        if not read.isprintable():
            raise ValueError(f"A name reads at a table, and {offered!r} holds a character that shows nothing")

        return read
