from typing import Annotated

from pydantic import Field

from cardwork.models.base import BaseFrozen


class Dealing(BaseFrozen):
    """A guest calling for the deal, which opens the table and ends the gathering."""

    base_revision: Annotated[int, Field(ge=0)]
