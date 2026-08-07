from typing import Annotated

from pydantic import Field

from cardwork.models.base import BaseFrozen
from cardwork.presentation.tint import Tint


class Tinting(BaseFrozen):
    """A guest taking one of the company's tints, which is the mark the table tells them apart by."""

    tint: Tint
    base_revision: Annotated[int, Field(ge=0)]
