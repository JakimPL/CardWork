from http import HTTPStatus

from httpx import AsyncClient

from cardserver.sessions import TableSession
from cardwork.presentation.layout import Layout
from cardwork.states.state import GameState

from ..games.demo import SEATS, hand_of, tray_of
from .conftest import DEAL, LAYOUT, MOVES, UNSERVED, credentials, sealing
from .layout import SEALED_SCENE, TITLE

WATCHING: int | None = None
SEATED = 1


async def test_a_seat_reads_the_layout_of_the_scene_the_table_opened_with(client: AsyncClient) -> None:
    response = await client.get(LAYOUT, headers=credentials(SEATED))

    assert Layout.model_validate(response.json()) == SEALED_SCENE.layout(SEATS, SEATED)


async def test_a_layout_names_the_seat_it_was_built_for(client: AsyncClient) -> None:
    response = await client.get(LAYOUT, headers=credentials(SEATED))

    assert response.json()["observer"] == SEATED


async def test_a_layout_is_built_for_the_table_the_game_seats(client: AsyncClient) -> None:
    response = await client.get(LAYOUT, headers=credentials(SEATED))

    assert response.json()["players"] == SEATS


async def test_a_seat_lays_out_the_zones_it_holds_of_its_own(client: AsyncClient) -> None:
    response = await client.get(LAYOUT, headers=credentials(SEATED))

    laid = {slot["zone"] for slot in response.json()["slots"]}
    assert {hand_of(SEATED), tray_of(SEATED)} <= laid


async def test_a_seat_lays_out_the_zones_of_every_other_seat_under_that_seat(client: AsyncClient) -> None:
    response = await client.get(LAYOUT, headers=credentials(SEATED))

    owners = {slot["zone"]: slot["seat"] for slot in response.json()["slots"]}
    assert {hand_of(seat): seat for seat in range(SEATS)}.items() <= owners.items()


async def test_a_spectator_reads_the_zones_the_table_shares(client: AsyncClient) -> None:
    response = await client.get(LAYOUT)

    assert Layout.model_validate(response.json()) == SEALED_SCENE.layout(SEATS, WATCHING)


async def test_a_spectator_is_offered_no_gesture(client: AsyncClient) -> None:
    response = await client.get(LAYOUT)

    assert response.json()["gestures"] == []


async def test_a_layout_carries_the_title_the_game_states(client: AsyncClient) -> None:
    response = await client.get(LAYOUT)

    assert response.json()["title"] == TITLE


async def test_a_layout_holds_a_plaque_for_every_seat(client: AsyncClient) -> None:
    response = await client.get(LAYOUT)

    assert [plaque["seat"] for plaque in response.json()["plaques"]] == list(range(SEATS))


async def test_a_layout_stands_as_the_cards_move(client: AsyncClient) -> None:
    before = await client.get(LAYOUT, headers=credentials(0))
    await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))

    after = await client.get(LAYOUT, headers=credentials(0))

    assert after.json() == before.json()


async def test_a_layout_of_a_table_out_of_service_is_refused(client: AsyncClient) -> None:
    response = await client.get(f"/tables/{UNSERVED}/layout")

    assert response.status_code == HTTPStatus.NOT_FOUND


async def test_a_session_lays_its_table_out_for_the_seats_the_game_holds(
    session: TableSession[GameState],
) -> None:
    assert session.layout(SEATED) == SEALED_SCENE.layout(SEATS, SEATED)
