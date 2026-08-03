from pydantic import Field

from cardwork.models.base import BaseFrozen
from cardwork.presentation.tally import Tally


class Plaque(BaseFrozen):
    """One player as the whole table reads them: the seat, the name it plays under, and the zones it holds.

    Every seat takes a plaque, the observer's own among them, so the standing reads across the table in one
    row. What the plaque shows beside the counts — the score, a game's own per-seat tally — comes from the
    readouts scoped to a seat, which leaves a plaque stating who is there rather than what is worth showing.
    """

    seat: int = Field(ge=0)
    name: str
    counts: tuple[Tally, ...]
