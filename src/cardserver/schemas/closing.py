from typing import Annotated, Final

from pydantic import Field

from cardwork.models.base import BaseFrozen

REASON_LONGEST: Final[int] = 200  # TODO: move to advanced server configuration


class Closing(BaseFrozen):
    """Breaking a table up, with a word for the company on why, which the host or an admin may call for."""

    reason: Annotated[str, Field(max_length=REASON_LONGEST)] | None = None
