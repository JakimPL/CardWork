from http import HTTPStatus

import pytest
from httpx import AsyncClient

from cardserver.identity import SEAT_HEADER
from cardserver.sessions import TableSession
from cardwork.moves.actions import Play
from cardwork.moves.move import Move
from cardwork.states.state import GameState

from ..games.demo import SEATS
from .conftest import DEAL, MOVES, command, credentials, reclaiming, sealing


async def test_a_seat_s_move_is_answered_with_the_sequence_it_landed_at(client: AsyncClient) -> None:
    response = await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"seq": DEAL}


async def test_a_committed_move_reaches_the_table(client: AsyncClient, session: TableSession[GameState]) -> None:
    await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))

    assert session.head == DEAL + 1


async def test_a_move_built_on_a_superseded_position_is_refused(client: AsyncClient) -> None:
    await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))

    response = await client.post(MOVES, json=sealing(1, DEAL, "second"), headers=credentials(1))

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["error"] == "StalePosition"


async def test_a_seat_that_has_acted_is_refused_the_turn(client: AsyncClient) -> None:
    await client.post(MOVES, json=sealing(0, DEAL, "first"), headers=credentials(0))

    response = await client.post(MOVES, json=sealing(0, DEAL + 1, "again"), headers=credentials(0))

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["error"] == "NotYourTurn"


async def test_a_move_the_rules_reject_is_refused(client: AsyncClient) -> None:
    beyond_the_hand = Move(player=0, action=Play(group="sealed", indices=frozenset({99})))

    response = await client.post(MOVES, json=command(beyond_the_hand, DEAL, "first"), headers=credentials(0))

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["error"] == "IllegalMove"


async def test_a_seat_with_nothing_sealed_is_refused_a_take_back(client: AsyncClient) -> None:
    response = await client.post(MOVES, json=reclaiming(0, DEAL, "first"), headers=credentials(0))

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"base_seq": DEAL, "idempotency_key": "first"}, id="a command naming no move"),
        pytest.param({"move": {"player": 0}, "base_seq": DEAL, "idempotency_key": "x"}, id="a move with no action"),
        pytest.param({**sealing(0, DEAL, "first"), "table": "elsewhere"}, id="a command carrying a stray field"),
    ],
)
async def test_a_command_the_schema_rejects_is_refused(client: AsyncClient, body: dict[str, object]) -> None:
    response = await client.post(MOVES, json=body, headers=credentials(0))

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_a_seat_may_not_act_for_another(client: AsyncClient) -> None:
    response = await client.post(MOVES, json=sealing(1, DEAL, "first"), headers=credentials(0))

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["error"] == "WrongSeat"


async def test_a_spectator_may_not_act(client: AsyncClient) -> None:
    response = await client.post(MOVES, json=sealing(0, DEAL, "first"))

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["error"] == "WrongSeat"


async def test_an_unrecognised_credential_is_turned_away(client: AsyncClient) -> None:
    response = await client.post(MOVES, json=sealing(0, DEAL, "first"), headers={SEAT_HEADER: "picked-up-somewhere"})

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["error"] == "Unauthenticated"


async def test_a_refused_move_leaves_the_table_where_it_stood(
    client: AsyncClient, session: TableSession[GameState]
) -> None:
    beyond_the_hand = Move(player=0, action=Play(group="sealed", indices=frozenset({99})))

    await client.post(MOVES, json=command(beyond_the_hand, DEAL, "first"), headers=credentials(0))

    assert session.head == DEAL


async def test_a_retried_command_is_answered_with_the_sequence_it_first_reached(client: AsyncClient) -> None:
    retried = sealing(0, DEAL, "the-same-attempt")
    first = await client.post(MOVES, json=retried, headers=credentials(0))

    again = await client.post(MOVES, json=retried, headers=credentials(0))

    assert again.status_code == HTTPStatus.OK
    assert again.json() == first.json()


async def test_a_retried_command_lands_once(client: AsyncClient, session: TableSession[GameState]) -> None:
    retried = sealing(0, DEAL, "the-same-attempt")

    await client.post(MOVES, json=retried, headers=credentials(0))
    await client.post(MOVES, json=retried, headers=credentials(0))

    assert session.head == DEAL + 1


async def test_every_seat_may_seal_a_card_of_its_own(client: AsyncClient, session: TableSession[GameState]) -> None:
    for seat in range(SEATS):
        response = await client.post(MOVES, json=sealing(seat, session.head, f"seal-{seat}"), headers=credentials(seat))
        assert response.status_code == HTTPStatus.OK
