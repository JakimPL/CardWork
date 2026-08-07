from typing import Annotated

from pydantic import Field

from cardserver.schemas.choice import Choice
from cardwork.models.base import BaseFrozen


class Choosing(BaseFrozen):
    """A guest settling what the table plays."""

    choice: Choice
    base_revision: Annotated[int, Field(ge=0)]
