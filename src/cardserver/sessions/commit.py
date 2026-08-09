from typing import Protocol

from cardwork.views.event import ZoneChange


class Commit(Protocol):
    """One commit on its way to a client: where it landed, what it moved, and the body a frame carries.

    The cursor a commit leaves is the one part of it a game settles the shape of. Where it landed and which
    cards moved read alike at every table, so they stand here and the cursor goes out inside the body.
    """

    @property
    def seq(self) -> int:
        """The sequence the commit landed at, which is the id its frame is keyed by."""

    @property
    def changes(self) -> tuple[ZoneChange, ...]:
        """Which zones the commit moved cards in, as the observer it was read for learns of them."""

    def model_dump_json(self) -> str:
        """The commit as the wire carries it."""
