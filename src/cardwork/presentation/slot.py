from pydantic import Field

from cardwork.models.base import BaseFrozen
from cardwork.presentation.spread import Spread
from cardwork.zones.zone import ZoneId


class Slot(BaseFrozen):
    """One zone laid out: whose it is, how its cards lie against each other, and what it is called.

    `seat` names the owner of the zone, and None a zone the seats share and every one of them reads the same
    way: the pile dealt from, the stack laid on. Where an owner's zones go on the page is the interface's own —
    the seat reading the layout holds one place, each of the others another, and the shared zones the middle —
    which is why one number carries the whole of the geography a game states.

    `place` orders the slots one owner holds, counting from the first. `counted` shows how many cards the zone
    holds, which is what a heap of backs has to say for itself and a hand of three states by lying there.
    Whether a slot may be selected from or committed onto follows from the gestures naming it, so a slot states
    where its cards are and leaves what they afford to the moves the rules admit.
    """

    zone: ZoneId
    label: str
    seat: int | None
    spread: Spread
    place: int = Field(ge=0)
    counted: bool
