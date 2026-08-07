from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from random import Random
from typing import Final

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from cardserver.app import create_app
from cardserver.identity import SEAT_HEADER, TokenSeats
from cardserver.protocol import Presentation, Table
from cardserver.registry import TableRegistry
from cardserver.schemas import ArrangementRequest, Arriving, Claiming, MoveRequest, Readying
from cardserver.sessions import InService, TableSession
from cardwork.decks.deck import Order
from cardwork.moves.actions import Play, Take
from cardwork.moves.move import Move
from cardwork.states.state import GameState
from cardwork.zones.zone import ZoneId
from cardwork.zones.zones import hand_of

from ..games.demo import DECK, HAND_SIZE, SEATS, SealedRoundGame
from .company import CODE, Gathered, gathered
from .layout import SEALED_SCENE

TABLE: Final[str] = "green-baize"
UNSERVED: Final[str] = "no-such-table"
SEED: Final[int] = 20260802
NO_GRACE: Final[float] = 0.0
LONG_GRACE: Final[float] = 30.0
FIRST_CARD: Final[frozenset[int]] = frozenset({0})
DEAL: Final[int] = 1
BASE_URL: Final[str] = "http://cardwork"

BACKWARDS: Final[Order] = tuple(reversed(range(HAND_SIZE)))

MOVES: Final[str] = f"/tables/{TABLE}/moves"
ARRANGEMENTS: Final[str] = f"/tables/{TABLE}/arrangements"
LAYOUT: Final[str] = f"/tables/{TABLE}/layout"
VIEW: Final[str] = f"/tables/{TABLE}/view"
EVENTS: Final[str] = f"/tables/{TABLE}/events"
JOURNAL: Final[str] = f"/tables/{TABLE}/journal"

OFFERED: Final[str] = "/offerings"
TABLES: Final[str] = "/tables"
GUESTS: Final[str] = f"/tables/{TABLE}/guests"
GATHERING: Final[str] = f"/tables/{TABLE}/gathering"
ATTENDANCE: Final[str] = f"/tables/{TABLE}/gathering/events"
SEAT: Final[str] = f"/tables/{TABLE}/seat"
TINT: Final[str] = f"/tables/{TABLE}/tint"
CHOICE: Final[str] = f"/tables/{TABLE}/choice"
DEALING: Final[str] = f"/tables/{TABLE}/deal"
READY: Final[str] = f"/tables/{TABLE}/ready"
GOVERNANCE: Final[str] = f"/tables/{TABLE}/governance"
CLOSING: Final[str] = f"/tables/{TABLE}/closing"


def token_of(seat: int) -> str:
    return f"token-for-seat-{seat}"


def holding(token: str) -> dict[str, str]:
    """The header a client speaks its token through, whichever half of the protocol it is asking for."""
    return {SEAT_HEADER: token}


def credentials(seat: int) -> dict[str, str]:
    return holding(token_of(seat))


def command(move: Move, base_seq: int, key: str) -> dict[str, object]:
    """A command in the shape a client sends it, built through the schema the server validates it with."""
    return MoveRequest(move=move, base_seq=base_seq, idempotency_key=key).model_dump(mode="json")


def sealing(seat: int, base_seq: int, key: str) -> dict[str, object]:
    """A command sealing the first card of a seat's hand in its own tray."""
    return command(
        Move(player=seat, action=Play(group="sealed", indices=FIRST_CARD)),
        base_seq,
        key,
    )


def reclaiming(seat: int, base_seq: int, key: str) -> dict[str, object]:
    """A command lifting a seat's sealed card back into its hand."""
    return command(
        Move(player=seat, action=Take(group="sealed", indices=FIRST_CARD)),
        base_seq,
        key,
    )


def arranging(zone: ZoneId, order: Order, base_seq: int, key: str) -> dict[str, object]:
    """A command laying one zone out in an order, built through the schema the server validates it with.

    The seat is absent as it is absent from the wire: the server reads it off the credential the request
    carries, so a client states the zone alone and the token settles whose zone that is.
    """
    return ArrangementRequest(zone=zone, order=order, base_seq=base_seq, idempotency_key=key).model_dump(mode="json")


def sorting(seat: int, base_seq: int, key: str) -> dict[str, object]:
    """A command laying a seat's own hand out back to front, which is the order a full hand reverses into."""
    return arranging(hand_of(seat), BACKWARDS, base_seq, key)


@asynccontextmanager
async def served[StateT: GameState](
    table: Table[StateT],
    presentation: Presentation,
) -> AsyncIterator[tuple[AsyncClient, TableSession[StateT]]]:
    """One game in service under `TABLE`, answering as the client a seat speaks through and the session behind it.

    A game arrives with a state type of its own, and the registry, the application and the projection carry
    that type out to the wire, which is what a real game served in its own module reads for. The window is
    left at nothing, so a round closed by the last seat to act settles as soon as the session is drained.
    """
    registry = TableRegistry(NO_GRACE)
    session = registry.open(TABLE, table, presentation)
    seats = TokenSeats({TABLE: {token_of(seat): seat for seat in range(table.players)}})
    app = create_app(registry, seats, None)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url=BASE_URL,
        ) as client:
            yield client, session
    finally:
        await registry.close()


async def close_the_round(client: AsyncClient, session: InService) -> None:
    """Seal a card at every seat, which leaves the round closed and waiting on the window."""
    for seat in range(SEATS):
        await client.post(
            MOVES,
            json=sealing(seat, session.head, f"seal-{seat}"),
            headers=credentials(seat),
        )


@pytest.fixture(name="grace")
def grace_fixture() -> float:
    return NO_GRACE


@pytest.fixture(name="registry")
async def registry_fixture(grace: float) -> AsyncIterator[TableRegistry]:
    registry = TableRegistry(grace)
    registry.open(
        TABLE,
        SealedRoundGame(players=SEATS, deck=DECK, rng=Random(SEED)),
        SEALED_SCENE,
    )

    yield registry

    await registry.close()


@pytest.fixture(name="session")
def session_fixture(registry: TableRegistry) -> InService:
    return registry.session(TABLE)


@pytest.fixture(name="app")
def app_fixture(registry: TableRegistry) -> FastAPI:
    seats = TokenSeats({TABLE: {token_of(seat): seat for seat in range(SEATS)}})
    return create_app(registry, seats, None)


@pytest.fixture(name="client")
async def client_fixture(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE_URL,
    ) as client:
        yield client


async def arriving(client: AsyncClient, name: str) -> Response:
    """One person arriving at the table on its own code, built through the schema the server validates it with."""
    return await client.post(GUESTS, json=Arriving(code=CODE, name=name).model_dump(mode="json"))


async def arrives(client: AsyncClient, name: str) -> str:
    """The token one guest's arrival minted, which is what they speak through afterwards."""
    return str((await arriving(client, name)).json()["token"])


async def sits(client: AsyncClient, token: str, seat: int | None, base_revision: int) -> Response:
    """One guest taking a seat at the gathering, or standing up from the one they hold by naming none."""
    return await client.put(
        SEAT,
        json=Claiming(seat=seat, base_revision=base_revision).model_dump(mode="json"),
        headers=holding(token),
    )


async def readies(client: AsyncClient, token: str, base_revision: int) -> Response:
    """One seated guest committing to the settings as they stand."""
    return await client.put(
        READY,
        json=Readying(ready=True, base_revision=base_revision).model_dump(mode="json"),
        headers=holding(token),
    )


async def seated_company(
    client: AsyncClient,
    names: tuple[str, ...],
) -> tuple[str, ...]:
    """A company arriving one after another, taking the seats in order and committing to the settings.

    Every seat of the table the gathering settled comes to be held and every one of them commits, which leaves
    the deal to be called for and nothing standing in its way. Each command quotes the revision the one before
    it answered with, so the whole company is seated and ready by the time the deal is asked for.
    """
    tokens: list[str] = []
    for seat, name in enumerate(names):
        admitted = (await arriving(client, name)).json()
        await sits(client, admitted["token"], seat, admitted["gathering"]["revision"])
        tokens.append(str(admitted["token"]))

    for token in tokens:
        reached = (await client.get(GATHERING, headers=holding(token))).json()
        await readies(client, token, reached["revision"])

    return tuple(tokens)


@pytest.fixture(name="gathered")
async def gathered_fixture() -> AsyncIterator[Gathered]:
    held = gathered(TABLE, SEATS)

    yield held

    await held.registry.close()


@pytest.fixture(name="visitor")
async def visitor_fixture(gathered: Gathered) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=gathered.app),
        base_url=BASE_URL,
    ) as client:
        yield client
