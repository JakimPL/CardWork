import json
from http import HTTPStatus
from typing import Any, Final

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from cardserver.sessions import TableSession
from cardserver.streams import frame, resume_point
from cardwork.states.state import GameState

from ..games.demo import tray_of
from .conftest import DEAL, EVENTS, MOVES, credentials, sealing
from .harness import Streamed

DATA: Final[str] = "data: "
RESUME_HEADER: Final[str] = "Last-Event-ID"


def payload(written: str) -> dict[str, Any]:
    """The event carried by one frame, read the way a client reads the data line of it."""
    lines = [line for line in written.splitlines() if line.startswith(DATA)]
    return dict(json.loads(lines[0].removeprefix(DATA)))


def after(written: str, zone: str) -> list[Any]:
    """How one zone reads once the commit in this frame has landed."""
    changes = [change for change in payload(written)["changes"] if change["zone"] == zone]
    return list(changes[0]["after"])


async def test_a_stream_opens_with_the_commits_already_made(app: FastAPI) -> None:
    async with Streamed(app, EVENTS, credentials(0)) as stream:
        status = await stream.status()
        written = await stream.frame()

    assert status == HTTPStatus.OK
    assert written.startswith(f"id: 0\nevent: commit\n{DATA}")


async def test_a_stream_carries_a_commit_as_it_lands(app: FastAPI, client: AsyncClient) -> None:
    async with Streamed(app, EVENTS, credentials(0)) as stream:
        await stream.status()
        await stream.frame()

        await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))
        landed = await stream.frame()

    assert payload(landed)["seq"] == DEAL


async def test_a_stream_resumes_after_the_last_commit_a_client_read(app: FastAPI, client: AsyncClient) -> None:
    await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))

    async with Streamed(app, EVENTS, {**credentials(0), RESUME_HEADER: "0"}) as stream:
        await stream.status()
        written = await stream.frame()

    assert payload(written)["seq"] == DEAL


async def test_a_stream_may_be_asked_to_start_from_a_point(app: FastAPI, client: AsyncClient) -> None:
    await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))

    async with Streamed(app, f"{EVENTS}?since={DEAL}", credentials(0)) as stream:
        await stream.status()
        written = await stream.frame()

    assert payload(written)["seq"] == DEAL


async def test_a_stream_names_the_observer_it_was_built_for(app: FastAPI) -> None:
    async with Streamed(app, EVENTS, credentials(2)) as stream:
        await stream.status()
        written = await stream.frame()

    assert payload(written)["observer"] == 2


async def test_a_stream_names_a_sealed_card_to_the_seat_that_sealed_it(app: FastAPI, client: AsyncClient) -> None:
    await client.post(MOVES, json=sealing(1, DEAL, "first"), headers=credentials(1))

    async with Streamed(app, f"{EVENTS}?since={DEAL}", credentials(1)) as stream:
        await stream.status()
        written = await stream.frame()

    assert after(written, tray_of(1)) != [None]


async def test_a_stream_shows_everyone_else_a_count_where_it_lies(app: FastAPI, client: AsyncClient) -> None:
    await client.post(MOVES, json=sealing(1, DEAL, "first"), headers=credentials(1))

    async with Streamed(app, f"{EVENTS}?since={DEAL}", {}) as stream:
        await stream.status()
        written = await stream.frame()

    assert after(written, tray_of(1)) == [None]


@pytest.mark.parametrize(
    ("last_event_id", "since", "expected"),
    [
        pytest.param(None, 0, 0, id="a client with nothing to resume from"),
        pytest.param(None, 7, 7, id="a client naming where to start"),
        pytest.param(3, 0, 4, id="a client resuming after the commit it read"),
        pytest.param(3, 7, 4, id="a resumed client, which knows better than the point it asked for"),
    ],
)
def test_a_stream_picks_up_where_a_client_left_off(last_event_id: int | None, since: int, expected: int) -> None:
    assert resume_point(last_event_id, since) == expected


async def test_a_frame_carries_the_sequence_as_the_id_a_client_hands_back(
    session: TableSession[GameState],
) -> None:
    written = frame(session.events(0, 0)[0])

    assert written.startswith("id: 0\n")
    assert written.endswith("\n\n")
