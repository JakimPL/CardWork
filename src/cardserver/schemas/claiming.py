from typing import Annotated

from pydantic import Field

from cardwork.models.base import BaseFrozen


class Claiming(BaseFrozen):
    """A guest taking a seat, or standing up from the one they hold by naming none."""

    seat: Annotated[int, Field(ge=0)] | None
    base_revision: Annotated[int, Field(ge=0)]
