from http import HTTPStatus

from httpx import AsyncClient

from cardserver.identity import SEAT_HEADER
from cardserver.sessions import TableSession
from cardwork.states.state import GameState

from ..games.demo import HAND_SIZE, SEATS, hand_of
from .conftest import DEAL, MOVES, UNSERVED, VIEW, credentials, sealing


async def test_a_seat_reads_the_hand_it_holds(client: AsyncClient) -> None:
    response = await client.get(VIEW, headers=credentials(0))

    cards = response.json()["zones"][hand_of(0)]["cards"]
    assert len(cards) == HAND_SIZE
    assert all(card is not None for card in cards)


async def test_a_seat_reads_a_count_where_another_hand_lies(client: AsyncClient) -> None:
    response = await client.get(VIEW, headers=credentials(0))

    assert response.json()["zones"][hand_of(1)]["cards"] == [None] * HAND_SIZE


async def test_a_spectator_reads_a_count_at_every_hand(client: AsyncClient) -> None:
    response = await client.get(VIEW)

    zones = response.json()["zones"]
    assert all(zones[hand_of(seat)]["cards"] == [None] * HAND_SIZE for seat in range(SEATS))


async def test_a_view_names_the_seat_it_was_built_for(client: AsyncClient) -> None:
    response = await client.get(VIEW, headers=credentials(2))

    assert response.json()["observer"] == 2


async def test_a_spectator_is_named_as_one(client: AsyncClient) -> None:
    response = await client.get(VIEW)

    assert response.json()["observer"] is None


async def test_a_view_is_stamped_with_the_sequence_it_stands_at(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    response = await client.get(VIEW, headers=credentials(0))

    assert response.json()["seq"] == session.head


async def test_a_view_follows_the_commits_that_land(client: AsyncClient) -> None:
    await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))

    response = await client.get(VIEW, headers=credentials(0))

    assert response.json()["seq"] == DEAL + 1


async def test_a_table_out_of_service_is_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/tables/{UNSERVED}/view")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["error"] == "UnknownTable"


async def test_an_unrecognised_credential_reads_nothing(client: AsyncClient) -> None:
    response = await client.get(VIEW, headers={SEAT_HEADER: "picked-up-somewhere"})

    assert response.status_code == HTTPStatus.UNAUTHORIZED
