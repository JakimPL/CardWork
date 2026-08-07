from typing import Annotated

from pydantic import Field

from cardserver.creation import Creation
from cardwork.models.base import BaseFrozen


class Advanced(BaseFrozen):
    """The tuning one run answers under: how a code is guarded, who governs a table, and how an empty lobby clears.

    A file states these the way it states the table and the service, so the values a person turns to harden a
    public deployment stand in the one place the rest of the run is read from. Each field is asked for outright,
    so a value the file leaves out is refused as the file is read rather than met as a surprise in service.

    A window and an allowance are what a code is guarded by: a caller offering more wrong codes than the allowance
    inside the window is turned away until the window runs out. The sweep is how long the lobby waits between one
    clearing of the tables nobody is at and the next, and the stale and idle spans are how long a gathering nobody
    holds and a table nobody commits to linger before that clearing takes them. Whether a table opens democratic,
    who may gather one at all, and how many may stand at once are the terms a run governs its lobby by until an
    overseer settles otherwise; a run stating no cap lets the lobby grow as far as the machine carries it.
    """

    turnstile_window: float = Field(gt=0.0)
    wrong_codes_allowed: int = Field(ge=1)
    sweep_seconds: float = Field(gt=0.0)
    democratic: bool
    creation: Creation
    capacity: Annotated[int, Field(ge=1)] | None
    stale_seconds: float = Field(gt=0.0)
    idle_seconds: float = Field(gt=0.0)
