from typing import Annotated, Final

from pydantic import Field

from cardserver.creation import Creation
from cardwork.models.base import BaseFrozen

NO_LIMIT: Final[int] = 0


class LobbySetting(BaseFrozen):
    """A change to the terms the lobby is held under, which the overseer settles a field at a time."""

    capacity: Annotated[int, Field(ge=NO_LIMIT)] | None = None
    creation: Creation | None = None
