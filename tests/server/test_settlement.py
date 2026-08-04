from http import HTTPStatus

from httpx import AsyncClient

from cardserver.sessions import TableSession
from cardwork.states.state import GameState

from ..games.demo import SEATS
from .conftest import (
    DEAL,
    JOURNAL,
    MOVES,
    VIEW,
    close_the_round,
    credentials,
    reclaiming,
    sealing,
)


async def test_the_rules_close_the_round_once_the_window_has_passed(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await close_the_round(client, session)

    await session.drain()

    response = await client.get(VIEW, headers=credentials(0))
    assert response.json()["state"]["phase"] == "score"


async def test_a_closed_round_scores_every_seat(client: AsyncClient, session: TableSession[GameState]) -> None:
    await close_the_round(client, session)
    await session.drain()

    response = await client.get(VIEW, headers=credentials(0))

    assert len(response.json()["state"]["points"]) == SEATS


async def test_the_rules_lay_every_sealed_card_face_up(client: AsyncClient, session: TableSession[GameState]) -> None:
    await close_the_round(client, session)
    await session.drain()

    response = await client.get(VIEW)

    discard = response.json()["zones"]["discard"]["cards"]
    assert len(discard) == SEATS
    assert all(card is not None for card in discard)


async def test_the_settling_commit_is_the_rules_own_and_carries_no_move(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await close_the_round(client, session)
    await session.drain()
    session.reveal()

    response = await client.get(JOURNAL)

    assert response.json()["transactions"][-1]["move"] is None


async def test_a_take_back_is_refused_once_the_round_has_closed(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await close_the_round(client, session)
    await session.drain()

    response = await client.post(MOVES, json=reclaiming(1, session.head, "late"), headers=credentials(1))

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_a_window_passing_over_a_round_in_play_settles_nothing(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))

    await session.drain()

    assert session.head == DEAL + 1


async def test_a_table_nobody_has_played_at_settles_nothing(session: TableSession[GameState]) -> None:
    await session.drain()

    assert session.head == DEAL
