from enum import StrEnum
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
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

    @property
    def reported(self) -> int:
        """The level the standard library reads this as, which is what the table's own log is held to.

        The server states one level finer than the library holds names for, and a run asking for that reads
        everything the library has, which is its debug.
        """
        match self:
            case LogLevel.CRITICAL:
                return CRITICAL
            case LogLevel.ERROR:
                return ERROR
            case LogLevel.WARNING:
                return WARNING
            case LogLevel.INFO:
                return INFO
            case LogLevel.DEBUG | LogLevel.TRACE:
                return DEBUG


class Service(BaseFrozen):
    """Where a table answers, where it says it answers, and how much it says while it does.

    The address is asked for outright, so a run reachable from the machine alone and a run reachable from a
    network are told apart in a file that states which it is. The port stands at a settled number, since a
    person opening a table locally reaches it where they reached the last one.

    Listening and being reached are two different addresses: a table bound to every interface of the machine
    answers at each of them and at none by that name, so `advertise` states the one a person is handed. A run
    stating none is handed the address the machine holds on its own network, which is what a table behind a
    router or a tunnel departs from.

    A run behind a reverse proxy names in `forwarded_allow_ips` the peers it trusts to have set the forwarding
    headers, so the caller a table counts a wrong code against is the guest on the far side of the proxy rather
    than the proxy every guest arrives through. The value is what uvicorn reads: one address, several parted by
    commas, or `*` to trust every peer. A run naming none trusts no forwarding header and counts each caller by
    the peer it is spoken to directly, which is what a table reached without a proxy in front of it holds to.
    """

    host: str = Field(min_length=1)
    port: int = Field(default=PORT, ge=LOWEST_PORT, le=HIGHEST_PORT)
    advertise: str | None
    log_level: LogLevel
    forwarded_allow_ips: str | None
