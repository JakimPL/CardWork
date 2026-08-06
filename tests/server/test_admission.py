from http import HTTPStatus
from typing import Final

from httpx import AsyncClient

from cardserver.gathering import COMPANY_MOST, TURNSTILE_WINDOW, WRONG_CODES_ALLOWED
from cardserver.schemas import NAME_LONGEST, Arriving

from .company import CODE, WRONG_CODE, Gathered
from .conftest import GATHERING, GUESTS, TABLE, arriving, holding

A_MOMENT: Final[float] = 1.0
NAMED: Final[str] = "Ada"


async def offering(client: AsyncClient, code: str, name: str) -> HTTPStatus:
    """The status a table answers someone arriving with, a code and a name at a time."""
    answered = await client.post(GUESTS, json={"code": code, "name": name})
    return HTTPStatus(answered.status_code)


async def test_the_code_admits_a_guest_and_mints_the_token_they_speak_through(visitor: AsyncClient) -> None:
    answered = await arriving(visitor, NAMED)
    admitted = answered.json()

    assert answered.status_code == HTTPStatus.OK
    assert admitted["token"]
    assert admitted["gathering"]["mine"] == NAMED


async def test_a_guest_arrives_standing_at_no_seat(visitor: AsyncClient) -> None:
    admitted = (await arriving(visitor, NAMED)).json()

    assert admitted["gathering"]["company"] == [{"name": NAMED, "seat": None, "present": False}]


async def test_a_guest_is_told_the_code_so_they_can_pass_it_on(visitor: AsyncClient) -> None:
    admitted = (await arriving(visitor, NAMED)).json()

    assert admitted["gathering"]["code"] == CODE


async def test_the_code_admits_however_a_person_wrote_it_down(visitor: AsyncClient) -> None:
    assert await offering(visitor, "k q-a_j 7 2", NAMED) == HTTPStatus.OK


async def test_another_hand_of_ranks_admits_nobody(visitor: AsyncClient) -> None:
    assert await offering(visitor, WRONG_CODE, NAMED) == HTTPStatus.FORBIDDEN


async def test_the_room_is_shut_to_a_client_holding_no_token(visitor: AsyncClient) -> None:
    answered = await visitor.get(GATHERING)

    assert answered.status_code == HTTPStatus.UNAUTHORIZED


async def test_a_token_the_gathering_never_minted_is_turned_away(visitor: AsyncClient) -> None:
    answered = await visitor.get(GATHERING, headers=holding("picked-up-somewhere"))

    assert answered.status_code == HTTPStatus.UNAUTHORIZED


async def test_a_table_this_host_gathers_nowhere_is_named_in_the_refusal(visitor: AsyncClient) -> None:
    answered = await visitor.post("/tables/no-such-table/guests", json={"code": CODE, "name": NAMED})

    assert answered.status_code == HTTPStatus.NOT_FOUND


async def test_a_name_already_read_at_the_table_admits_nobody_else(visitor: AsyncClient) -> None:
    await arriving(visitor, NAMED)

    assert await offering(visitor, CODE, NAMED) == HTTPStatus.CONFLICT


async def test_a_name_reads_at_a_table_or_admits_nobody(visitor: AsyncClient) -> None:
    assert await offering(visitor, CODE, "   ") == HTTPStatus.UNPROCESSABLE_ENTITY
    assert await offering(visitor, CODE, "Ada\tLovelace") == HTTPStatus.UNPROCESSABLE_ENTITY
    assert await offering(visitor, CODE, "A" * (NAME_LONGEST + 1)) == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_a_name_is_read_with_the_space_around_it_trimmed_off(visitor: AsyncClient) -> None:
    admitted = (await visitor.post(GUESTS, json={"code": CODE, "name": f"  {NAMED}  "})).json()

    assert admitted["gathering"]["mine"] == NAMED


async def test_a_field_the_gathering_never_asked_for_admits_nobody(visitor: AsyncClient) -> None:
    answered = await visitor.post(GUESTS, json={"code": CODE, "name": NAMED, "seat": 0})

    assert answered.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_a_company_is_gathered_up_to_the_room_it_holds(visitor: AsyncClient) -> None:
    for guest in range(COMPANY_MOST):
        assert await offering(visitor, CODE, f"guest-{guest}") == HTTPStatus.OK

    assert await offering(visitor, CODE, "one-too-many") == HTTPStatus.FORBIDDEN


async def test_a_caller_offering_wrong_codes_is_turned_away_from_the_right_one(visitor: AsyncClient) -> None:
    for attempt in range(WRONG_CODES_ALLOWED):
        assert await offering(visitor, WRONG_CODE, f"guest-{attempt}") == HTTPStatus.FORBIDDEN

    assert await offering(visitor, CODE, NAMED) == HTTPStatus.FORBIDDEN


async def test_a_caller_is_listened_to_again_once_the_window_has_run_out(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    for attempt in range(WRONG_CODES_ALLOWED):
        await offering(visitor, WRONG_CODE, f"guest-{attempt}")

    gathered.ticking.on(TURNSTILE_WINDOW + A_MOMENT)

    assert await offering(visitor, CODE, NAMED) == HTTPStatus.OK


async def test_a_code_read_short_of_the_allowance_costs_a_caller_nothing(visitor: AsyncClient) -> None:
    for attempt in range(WRONG_CODES_ALLOWED - 1):
        await offering(visitor, WRONG_CODE, f"guest-{attempt}")

    assert await offering(visitor, CODE, NAMED) == HTTPStatus.OK


async def test_a_gathering_reads_the_arrival_it_was_asked_for(visitor: AsyncClient, gathered: Gathered) -> None:
    await arriving(visitor, NAMED)

    assert gathered.gathering.seat_of(NAMED) is None
    assert gathered.gatherings.at(TABLE) is gathered.gathering


def test_an_arrival_names_the_guest_it_speaks_for() -> None:
    assert Arriving(code=CODE, name=f" {NAMED} ").name == NAMED
