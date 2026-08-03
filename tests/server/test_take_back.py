from http import HTTPStatus

import pytest
from httpx import AsyncClient

from cardserver.sessions import TableSession
from cardwork.states.state import GameState

from ..games.demo import HAND_SIZE, SEATS, hand_of, tray_of
from .conftest import DEAL, LONG_GRACE, MOVES, VIEW, close_the_round, credentials, reclaiming


@pytest.fixture(name="grace")
def grace_fixture() -> float:
    """A window wide enough that a round stays open for the whole of a test."""
    return LONG_GRACE


async def test_the_rules_wait_out_the_window_before_closing_a_round(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await close_the_round(client, session)

    response = await client.get(VIEW, headers=credentials(0))

    assert response.json()["state"]["phase"] == "play"


async def test_a_seat_may_take_its_commitment_back_inside_the_window(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await close_the_round(client, session)

    response = await client.post(MOVES, json=reclaiming(1, session.head, "reclaim"), headers=credentials(1))

    assert response.status_code == HTTPStatus.OK


async def test_a_take_back_hands_the_card_back_to_the_seat_that_sealed_it(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await close_the_round(client, session)
    await client.post(MOVES, json=reclaiming(1, session.head, "reclaim"), headers=credentials(1))

    response = await client.get(VIEW, headers=credentials(1))

    zones = response.json()["zones"]
    assert len(zones[hand_of(1)]["cards"]) == HAND_SIZE
    assert zones[tray_of(1)]["cards"] == []


async def test_a_take_back_reopens_the_turn_for_that_seat(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await close_the_round(client, session)
    await client.post(MOVES, json=reclaiming(1, session.head, "reclaim"), headers=credentials(1))

    response = await client.get(VIEW, headers=credentials(1))

    assert response.json()["state"]["to_act"] == [1]


async def test_a_take_back_only_adds_to_the_record(client: AsyncClient, session: TableSession[GameState]) -> None:
    await close_the_round(client, session)
    await client.post(MOVES, json=reclaiming(1, session.head, "reclaim"), headers=credentials(1))

    assert session.head == DEAL + SEATS + 1


async def test_a_seat_may_take_back_for_another_seat_at_no_point(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await close_the_round(client, session)

    response = await client.post(MOVES, json=reclaiming(1, session.head, "reclaim"), headers=credentials(0))

    assert response.status_code == HTTPStatus.FORBIDDEN
