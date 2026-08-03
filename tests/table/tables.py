from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from http import HTTPStatus
from typing import Final

from httpx import ASGITransport, AsyncClient

from cardgames.frontend.passing.layout import PASSING_SCENE
from cardgames.frontend.showdown.layout import SHOWDOWN_SCENE
from cardserver.identity import SEAT_HEADER
from cardserver.schemas import MoveRequest
from cardtable.catalogue import opened
from cardtable.games import GameName
from cardtable.hosting import Hosted
from cardtable.settings import Settings
from cardwork.presentation.scene import Scene

from ..cases import Case

TABLE: Final[str] = "green-baize"
UNSERVED: Final[str] = "no-such-table"
PLAYERS: Final[int] = 3
ROUNDS: Final[int] = 2
SEED: Final[int] = 20260803
NO_GRACE: Final[float] = 0.0
BASE_URL: Final[str] = "http://cardwork"

SETTINGS: Final[Settings] = Settings(
    name=TABLE,
    players=PLAYERS,
    rounds=ROUNDS,
    seed=SEED,
    grace_seconds=NO_GRACE,
)

LAYOUT: Final[str] = f"/tables/{TABLE}/layout"
VIEW: Final[str] = f"/tables/{TABLE}/view"
MOVES: Final[str] = f"/tables/{TABLE}/moves"


@dataclass(frozen=True)
class HostCase(Case):
    """One game the host holds, beside the scene its own module states for it.

    Naming the scene here rather than reading it back off the host is what makes the assertion say
    something: the layout a client is served has to be the one the game stated, not merely a layout.
    """

    game: GameName
    scene: Scene


CASES: Final[tuple[HostCase, ...]] = (
    HostCase(
        description="a game of four cards passed in turn",
        game=GameName.PASSING,
        scene=PASSING_SCENE,
    ),
    HostCase(
        description="a game of sealed cards turned over at once",
        game=GameName.SHOWDOWN,
        scene=SHOWDOWN_SCENE,
    ),
)


def credentials(hosted: Hosted, seat: int) -> dict[str, str]:
    """The header a client speaks for one seat of a hosted table through."""
    return {SEAT_HEADER: hosted.tokens[seat]}


@asynccontextmanager
async def playing(game: GameName) -> AsyncIterator[tuple[AsyncClient, Hosted]]:
    """One table of that game open through the host, answering as a client reaching it does.

    The application's own lifespan runs around the client, so the table ends these tests holding no timer
    the way it ends its service under a server.
    """
    hosted = opened(game, SETTINGS)
    async with hosted.app.router.lifespan_context(hosted.app):
        async with AsyncClient(transport=ASGITransport(app=hosted.app), base_url=BASE_URL) as client:
            yield client, hosted


async def a_seat_to_act(client: AsyncClient, hosted: Hosted) -> tuple[int, dict[str, object], int]:
    """A seat the table holds a move for, one of the moves it may make, and the sequence it stands at.

    The moves come from the seat's own view, which is how an interface reads them, so a seat found here is
    one a client would have been offered something to do.

    Raises:
        ValueError: when no seat of the table is offered a move, which a table in play never reaches.
    """
    for seat in range(PLAYERS):
        served = (await client.get(VIEW, headers=credentials(hosted, seat))).json()
        if served["legal"]:
            return seat, served["legal"][0], served["seq"]

    raise ValueError(f"Table {hosted.table!r} offers no seat a move to make")


async def submit(
    client: AsyncClient,
    hosted: Hosted,
    seat: int,
    move: dict[str, object],
    base_seq: int,
) -> HTTPStatus:
    """Send one move as the seat holding it, and answer with the status the table met it with."""
    command = MoveRequest.model_validate({"move": move, "base_seq": base_seq, "idempotency_key": "the-first-try"})
    response = await client.post(
        MOVES,
        json=command.model_dump(mode="json"),
        headers=credentials(hosted, seat),
    )
    return HTTPStatus(response.status_code)
