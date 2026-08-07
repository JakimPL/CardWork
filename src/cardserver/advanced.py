from pydantic import Field

from cardwork.models.base import BaseFrozen


class Advanced(BaseFrozen):
    """The tuning one run answers under: how hard a code is to guess at, and how often an empty lobby is cleared.

    A file states these the way it states the table and the service, so the values a person turns to harden a
    public deployment stand in the one place the rest of the run is read from. Each field is asked for outright,
    so a value the file leaves out is refused as the file is read rather than met as a surprise in service.

    A window and an allowance are what a code is guarded by: a caller offering more wrong codes than the allowance
    inside the window is turned away until the window runs out. The sweep is how long the lobby waits between one
    clearing of the tables nobody is at and the next.
    """

    turnstile_window: float = Field(gt=0.0)
    wrong_codes_allowed: int = Field(ge=1)
    sweep_seconds: float = Field(gt=0.0)
