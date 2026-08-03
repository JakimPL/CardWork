from http import HTTPStatus

from httpx import AsyncClient

from cardserver.sessions import TableSession
from cardwork.states.state import GameState

from ..games.demo import DECK, hand_of
from .conftest import DEAL, JOURNAL, MOVES, UNSERVED, credentials, sealing


async def test_the_record_stays_closed_while_the_game_is_on(client: AsyncClient) -> None:
    response = await client.get(JOURNAL)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["error"] == "JournalSealed"


async def test_a_seat_reads_no_more_of_the_record_than_a_spectator(client: AsyncClient) -> None:
    response = await client.get(JOURNAL, headers=credentials(0))

    assert response.status_code == HTTPStatus.FORBIDDEN


async def test_the_record_opens_once_the_host_calls_the_game_over(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    session.reveal()

    response = await client.get(JOURNAL)

    assert response.status_code == HTTPStatus.OK
    assert len(response.json()["transactions"]) == session.head


async def test_the_open_record_holds_the_deck_the_table_started_from(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    session.reveal()

    response = await client.get(JOURNAL)

    origin = response.json()["initial"]["board"]["zones"]
    assert len(origin["draw"]["cards"]) == len(DECK)
    assert origin[hand_of(0)]["cards"] == []


async def test_the_open_record_carries_every_move_that_was_made(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))
    session.reveal()

    response = await client.get(JOURNAL)

    assert response.json()["transactions"][DEAL]["move"]["player"] == 0


async def test_the_record_of_a_table_out_of_service_is_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/tables/{UNSERVED}/journal")

    assert response.status_code == HTTPStatus.NOT_FOUND
