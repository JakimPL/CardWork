from enum import StrEnum
from typing import Final

from pydantic import Field

from cardwork.models.base import BaseFrozen

PORT: Final[int] = 8000
LOWEST_PORT: Final[int] = 1
HIGHEST_PORT: Final[int] = 65535


class LogLevel(StrEnum):
    """How much of what a server does reaches a log, named as the server asks for it."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    TRACE = "trace"


class Service(BaseFrozen):
    """Where a table answers, and how much it says while it does.

    The address is asked for outright, so a run reachable from the machine alone and a run reachable from a
    network are told apart in a file that states which it is. The port stands at a settled number, since a
    person opening a table locally reaches it where they reached the last one.
    """

    host: str = Field(min_length=1)
    port: int = Field(default=PORT, ge=LOWEST_PORT, le=HIGHEST_PORT)
    log_level: LogLevel
