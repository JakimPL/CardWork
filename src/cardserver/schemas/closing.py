from typing import Annotated

from pydantic import Field

from cardserver.limits import REASON_LONGEST
from cardwork.models.base import BaseFrozen


class Closing(BaseFrozen):
    """Breaking a table up, with a word for the company on why, which the host or an admin may call for."""

    reason: Annotated[str, Field(max_length=REASON_LONGEST)] | None = None
