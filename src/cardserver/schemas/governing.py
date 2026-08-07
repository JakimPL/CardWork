from typing import Annotated

from pydantic import Field

from cardwork.models.base import BaseFrozen


class Governing(BaseFrozen):
    """The host settling how the table is governed: democratically, or by the host's own say alone."""

    democratic: bool
    base_revision: Annotated[int, Field(ge=0)]
