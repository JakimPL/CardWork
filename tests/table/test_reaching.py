from dataclasses import dataclass
from typing import Final, Self

import pytest

from cardtable import reaching
from cardtable.reaching import LOOPBACK, WILDCARDS, Probe, a_local_address, an_address, reached_at
from cardtable.service import LogLevel, Service
from tests.cases import Case, descriptions

PORT: Final[int] = 8421
BOUND: Final[str] = "192.168.1.42"
ANNOUNCED: Final[str] = "cardwork.local"
EVERYWHERE: Final[str] = "0.0.0.0"
NOWHERE: Final[None] = None
QUADS: Final[int] = 4


def a_service(host: str, advertise: str | None) -> Service:
    """A run listening at one address and saying it is reached at another, or saying nothing of it."""
    return Service(
        host=host,
        port=PORT,
        advertise=advertise,
        log_level=LogLevel.INFO,
    )


def holding(address: str | None) -> Probe:
    """A machine answering with that address of its own, which is what a probe reads off the route out."""
    return lambda: address


class Unrouted:
    """A socket on a machine holding no route out at all, which is what a probe meets with no network up."""

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_details: object) -> None:
        return None

    def connect(self, _address: tuple[str, int]) -> None:
        """Refuse the route, the way a machine with nowhere to send anything does.

        Raises:
            OSError: always, since there is no route to read an address off.
        """
        raise OSError("This machine holds no route to anywhere")


@dataclass(frozen=True)
class ReachingCase(Case):
    """One run's binding and advertisement, beside every address a person is handed for it."""

    host: str
    advertise: str | None
    local: str | None
    reached: tuple[str, ...]


CASES: Final[tuple[ReachingCase, ...]] = (
    ReachingCase(
        description="a run bound to the loopback alone",
        host=LOOPBACK,
        advertise=NOWHERE,
        local=BOUND,
        reached=(f"http://{LOOPBACK}:{PORT}",),
    ),
    ReachingCase(
        description="a run bound to one address of the machine",
        host=BOUND,
        advertise=NOWHERE,
        local=BOUND,
        reached=(f"http://{BOUND}:{PORT}",),
    ),
    ReachingCase(
        description="a run bound to every interface, which is reached over the network and at the keyboard",
        host=EVERYWHERE,
        advertise=NOWHERE,
        local=BOUND,
        reached=(f"http://{BOUND}:{PORT}", f"http://{LOOPBACK}:{PORT}"),
    ),
    ReachingCase(
        description="a run bound to every interface of a machine holding no address of its own",
        host=EVERYWHERE,
        advertise=NOWHERE,
        local=NOWHERE,
        reached=(f"http://{LOOPBACK}:{PORT}",),
    ),
    ReachingCase(
        description="a run stating where it is reached, which stands whatever it is bound to",
        host=EVERYWHERE,
        advertise=ANNOUNCED,
        local=BOUND,
        reached=(f"http://{ANNOUNCED}:{PORT}",),
    ),
    ReachingCase(
        description="a run behind a name, bound to the loopback and reached through a tunnel",
        host=LOOPBACK,
        advertise=ANNOUNCED,
        local=BOUND,
        reached=(f"http://{ANNOUNCED}:{PORT}",),
    ),
)


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
def test_a_run_is_reached_at_the_addresses_it_answers_on(case: ReachingCase) -> None:
    reached = reached_at(a_service(case.host, case.advertise), holding(case.local))

    assert reached == case.reached


def test_a_wildcard_is_the_one_binding_that_names_no_address_of_its_own() -> None:
    """Why a machine is asked for its own address at all: a table bound to every interface answers at none."""
    assert EVERYWHERE in WILDCARDS
    assert LOOPBACK not in WILDCARDS


def test_an_address_is_written_the_way_a_browser_reaches_it() -> None:
    assert an_address(BOUND, PORT) == f"http://{BOUND}:{PORT}"


def test_the_machine_answers_with_an_address_of_its_own_or_with_none() -> None:
    """The one thing a probe of the machine itself can be held to, since what it reads is the machine's."""
    read = a_local_address()

    assert read is None or len(read.split(".")) == QUADS


def test_a_machine_holding_no_route_out_answers_with_no_address(monkeypatch: pytest.MonkeyPatch) -> None:
    """A run on a machine off every network still announces the loopback, which is where it is reached."""
    monkeypatch.setattr(reaching, "socket", lambda family, kind: Unrouted())

    assert a_local_address() is None
    assert reached_at(a_service(EVERYWHERE, NOWHERE), a_local_address) == (an_address(LOOPBACK, PORT),)
