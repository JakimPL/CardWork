from http import HTTPStatus
from typing import Final

import pytest
from httpx import AsyncClient

from cardserver.sessions import TableSession
from cardwork.decks.deck import Order
from cardwork.states.state import GameState

from ..games.demo import HAND_SIZE, SEATS, hand_of, tray_of
from .conftest import (
    ARRANGEMENTS,
    DEAL,
    LONG_GRACE,
    MOVES,
    VIEW,
    arranging,
    close_the_round,
    credentials,
    reclaiming,
    sealing,
    sorting,
)

SORTER: Final[int] = 0
LEFT_IN_HAND: Final[Order] = tuple(reversed(range(HAND_SIZE - 1)))


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


async def test_a_move_opens_the_window_every_seat_takes_its_moment_in(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await client.post(MOVES, json=sealing(SORTER, DEAL, "sealed"), headers=credentials(SORTER))

    assert session.settling is True


async def test_an_arrangement_opens_no_window_of_its_own(client: AsyncClient, session: TableSession[GameState]) -> None:
    """A seat sorting its own cards commits nothing another seat could ask to have back, so the rules wait on
    nothing and the table is left holding no timer at all.
    """
    await client.post(ARRANGEMENTS, json=sorting(SORTER, DEAL, "sort"), headers=credentials(SORTER))

    assert session.settling is False


async def test_a_seat_may_sort_what_it_holds_while_the_round_waits_to_close(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await close_the_round(client, session)

    response = await client.post(
        ARRANGEMENTS,
        json=arranging(hand_of(SORTER), LEFT_IN_HAND, session.head, "sort"),
        headers=credentials(SORTER),
    )

    assert response.status_code == HTTPStatus.OK


async def test_sorting_a_hand_leaves_the_round_where_the_last_move_left_it(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    """The window a closed round is waiting out stands as the last move left it, so what is owed falls due
    when it was always going to.
    """
    await close_the_round(client, session)
    await client.post(
        ARRANGEMENTS,
        json=arranging(hand_of(SORTER), LEFT_IN_HAND, session.head, "sort"),
        headers=credentials(SORTER),
    )

    response = await client.get(VIEW, headers=credentials(SORTER))

    assert response.json()["state"]["phase"] == "play"
    assert session.settling is True
