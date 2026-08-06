from collections.abc import Callable
from socket import AF_INET, SOCK_DGRAM, socket
from typing import Final

from cardtable.service import Service

SCHEME: Final[str] = "http"
LOOPBACK: Final[str] = "127.0.0.1"
WILDCARDS: Final[frozenset[str]] = frozenset({"0.0.0.0", "::"})

ELSEWHERE: Final[str] = "192.0.2.1"
ELSEWHERE_PORT: Final[int] = 9

Probe = Callable[[], str | None]


def a_local_address() -> str | None:
    """The address this machine holds on its own network, and None where it holds none.

    The address is read off the route the machine would take to somewhere else, which is what tells the one
    interface a table is reached over from the several a machine holds. The address chosen to route towards is
    reserved for documentation and the socket carries no traffic, so nothing leaves the machine to learn this.
    """
    with socket(AF_INET, SOCK_DGRAM) as probe:
        try:
            probe.connect((ELSEWHERE, ELSEWHERE_PORT))
        except OSError:
            return None

        address: str = probe.getsockname()[0]
        return address


def reached_at(service: Service, probe: Probe) -> tuple[str, ...]:
    """Every address a browser reaches this table at, the likeliest one first.

    A run stating where it is reached is taken at its word, since a table behind a router or a tunnel is the
    one case a machine cannot answer for itself. A run bound to one address is reached there. A run bound to
    every interface of the machine is reached at the address it holds on its network, and at the loopback
    besides, so the person at the keyboard and the person on the other side of the room are both handed a line
    that opens.

    Args:
        service: where the table listens and what it says of it.
        probe: how the machine's own address is read, which a run holds to the machine it is on.
    """
    if service.advertise is not None:
        return (an_address(service.advertise, service.port),)

    if service.host not in WILDCARDS:
        return (an_address(service.host, service.port),)

    local = probe()
    reached = (LOOPBACK,) if local is None else (local, LOOPBACK)
    return tuple(an_address(host, service.port) for host in reached)


def an_address(host: str, port: int) -> str:
    """Where a table answers, as a browser reaches it."""
    return f"{SCHEME}://{host}:{port}"
