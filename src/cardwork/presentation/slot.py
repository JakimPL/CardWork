from pydantic import Field

from cardwork.models.base import BaseFrozen
from cardwork.presentation.region import Region
from cardwork.presentation.spread import Spread
from cardwork.zones.zone import ZoneId


class Slot(BaseFrozen):
    """One zone laid out: where it goes, how its cards lie against each other, and what it is called.

    `place` orders the slots sharing a region, counting from the first. `counted` shows how many cards the
    zone holds, which is what a heap of backs has to say for itself and a hand of three states by lying
    there. Whether a slot may be selected from or committed onto follows from the gestures naming it, so a
    slot states where its cards are and leaves what they afford to the moves the rules admit.
    """

    zone: ZoneId
    label: str
    region: Region
    spread: Spread
    place: int = Field(ge=0)
    counted: bool
