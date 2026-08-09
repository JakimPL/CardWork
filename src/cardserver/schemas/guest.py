from cardwork.models.base import BaseFrozen
from cardwork.presentation.tint import Tint


class Guest(BaseFrozen):
    """One person at a gathering as the company reads them: the name, the tint, the seat, and whether they are here.

    The name is what a guest arrived under and the whole of their identity at the table. The tint is what tells
    them apart from the rest of the company at a glance, and no two guests hold one. The seat is the one they
    have taken, and none while they are standing. Presence follows the stream a page holds open, so the company
    reads as the room does.

    `ready` is whether the guest has committed to the settings as they stand, which only a seated guest may do
    and any change to what is played or who plays it takes back. `host` marks the guest who gathered the table,
    whose say governs it while it is settled host by host rather than company-wide.
    """

    name: str
    tint: Tint
    seat: int | None
    present: bool
    ready: bool
    host: bool
