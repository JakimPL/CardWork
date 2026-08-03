from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from random import Random
from typing import Final

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from cardserver.app import create_app
from cardserver.identity import SEAT_HEADER, TokenSeats
from cardserver.protocol import Presentation, Table
from cardserver.registry import TableRegistry
from cardserver.schemas import MoveRequest
from cardserver.sessions import TableSession
from cardwork.moves.actions import Play, Take
from cardwork.moves.move import Move
from cardwork.states.state import GameState

from ..games.demo import DECK, SEATS, SealedRoundGame
from .layout import SEALED_SCENE

TABLE: Final[str] = "green-baize"
UNSERVED: Final[str] = "no-such-table"
SEED: Final[int] = 20260802
NO_GRACE: Final[float] = 0.0
LONG_GRACE: Final[float] = 30.0
FIRST_CARD: Final[frozenset[int]] = frozenset({0})
DEAL: Final[int] = 1
BASE_URL: Final[str] = "http://cardwork"

MOVES: Final[str] = f"/tables/{TABLE}/moves"
LAYOUT: Final[str] = f"/tables/{TABLE}/layout"
VIEW: Final[str] = f"/tables/{TABLE}/view"
EVENTS: Final[str] = f"/tables/{TABLE}/events"
JOURNAL: Final[str] = f"/tables/{TABLE}/journal"


def token_of(seat: int) -> str:
    return f"token-for-seat-{seat}"


def credentials(seat: int) -> dict[str, str]:
    return {SEAT_HEADER: token_of(seat)}


def command(move: Move, base_seq: int, key: str) -> dict[str, object]:
    """A command in the shape a client sends it, built through the schema the server validates it with."""
    return MoveRequest(move=move, base_seq=base_seq, idempotency_key=key).model_dump(mode="json")


def sealing(seat: int, base_seq: int, key: str) -> dict[str, object]:
    """A command sealing the first card of a seat's hand in its own tray."""
    return command(Move(player=seat, action=Play(group="sealed", indices=FIRST_CARD)), base_seq, key)


def reclaiming(seat: int, base_seq: int, key: str) -> dict[str, object]:
    """A command lifting a seat's sealed card back into its hand."""
    return command(Move(player=seat, action=Take(group="sealed", indices=FIRST_CARD)), base_seq, key)


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
    registry = TableRegistry[StateT](NO_GRACE)
    session = registry.open(TABLE, table, presentation)
    seats = TokenSeats({TABLE: {token_of(seat): seat for seat in range(table.players)}})
    app = create_app(registry, seats)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            yield client, session
    finally:
        await registry.close()


async def close_the_round(client: AsyncClient, session: TableSession[GameState]) -> None:
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
async def registry_fixture(grace: float) -> AsyncIterator[TableRegistry[GameState]]:
    registry = TableRegistry[GameState](grace)
    registry.open(TABLE, SealedRoundGame(players=SEATS, deck=DECK, rng=Random(SEED)), SEALED_SCENE)

    yield registry

    await registry.close()


@pytest.fixture(name="session")
def session_fixture(registry: TableRegistry[GameState]) -> TableSession[GameState]:
    return registry.session(TABLE)


@pytest.fixture(name="app")
def app_fixture(registry: TableRegistry[GameState]) -> FastAPI:
    seats = TokenSeats({TABLE: {token_of(seat): seat for seat in range(SEATS)}})
    return create_app(registry, seats)


@pytest.fixture(name="client")
async def client_fixture(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        yield client
