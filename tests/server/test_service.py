import asyncio

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from cardserver.sessions import InService

from .conftest import DEAL, LONG_GRACE, MOVES, credentials, sealing
from .harness import PATIENCE, run_lifespan


@pytest.fixture(name="grace")
def grace_fixture() -> float:
    """A window wide enough that a settlement is still in hand when service ends."""
    return LONG_GRACE


async def test_an_application_starts_and_shuts_down(app: FastAPI) -> None:
    assert await run_lifespan(app) == ["lifespan.startup.complete", "lifespan.shutdown.complete"]


async def test_ending_service_drops_a_timer_still_in_hand(
    app: FastAPI, client: AsyncClient, session: InService
) -> None:
    await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))

    await run_lifespan(app)

    await asyncio.wait_for(session.drain(), timeout=PATIENCE)
    assert session.head == DEAL + 1
