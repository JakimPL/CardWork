from typing import Annotated

from pydantic import Field

from cardserver.gathering.config import NO_LIMIT  # TODO: not a proper place
from cardserver.oversight.creation import Creation
from cardwork.models.base import BaseFrozen


class LobbySetting(BaseFrozen):
    """A change to the terms the lobby is held under, which the overseer settles a field at a time."""

    capacity: Annotated[int, Field(ge=NO_LIMIT)] | None = None
    creation: Creation | None = None
