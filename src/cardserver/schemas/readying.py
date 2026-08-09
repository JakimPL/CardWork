from typing import Annotated

from pydantic import Field

from cardwork.models.base import BaseFrozen


class Readying(BaseFrozen):
    """A seated guest committing to the settings as they stand, or taking that commitment back.

    Readiness is the guest's own word that the choice may be dealt, so it names where the gathering stood when
    the word was given: a setting changing under it is what takes the word back, and a stale one is refused
    rather than read as an answer to a question that has moved on.
    """

    ready: bool
    base_revision: Annotated[int, Field(ge=0)]
