from dataclasses import dataclass
from http import HTTPStatus
from typing import Final

import pytest
from httpx import AsyncClient

from cardserver.identity import SEAT_HEADER
from cardserver.sessions import InService
from cardwork.decks.deck import Order
from cardwork.zones.zone import ZoneId
from cardwork.zones.zones import hand_of

from ..games.demo import HAND_SIZE, SEATS, tray_of
from .conftest import (
    ARRANGEMENTS,
    BACKWARDS,
    DEAL,
    MOVES,
    VIEW,
    arranging,
    credentials,
    sealing,
    sorting,
)

SORTER: Final[int] = 0
LANDED: Final[int] = DEAL + 1


async def held_by(client: AsyncClient, seat: int) -> list[object]:
    """The cards one seat reads in its own hand, in the order they lie there."""
    response = await client.get(VIEW, headers=credentials(seat))
    return list(response.json()["zones"][hand_of(seat)]["cards"])


async def test_an_order_is_answered_with_the_sequence_it_landed_at(client: AsyncClient) -> None:
    response = await client.post(ARRANGEMENTS, json=sorting(SORTER, DEAL, "first"), headers=credentials(SORTER))

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"seq": DEAL}


async def test_an_arrangement_reaches_the_table(client: AsyncClient, session: InService) -> None:
    await client.post(ARRANGEMENTS, json=sorting(SORTER, DEAL, "first"), headers=credentials(SORTER))

    assert session.head == LANDED


async def test_the_cards_come_to_lie_in_the_order_the_seat_asked_for(client: AsyncClient) -> None:
    held = await held_by(client, SORTER)

    await client.post(ARRANGEMENTS, json=sorting(SORTER, DEAL, "first"), headers=credentials(SORTER))

    assert await held_by(client, SORTER) == [held[index] for index in BACKWARDS]


async def test_the_seat_arranging_comes_off_the_credential(client: AsyncClient) -> None:
    """Every seat sorts the hand its own token holds, which is the whole of what says whose hand it is."""
    for seat in range(SEATS):
        held = await held_by(client, seat)

        response = await client.post(
            ARRANGEMENTS,
            json=arranging(hand_of(seat), BACKWARDS, DEAL + seat, f"sort-{seat}"),
            headers=credentials(seat),
        )

        assert response.status_code == HTTPStatus.OK
        assert await held_by(client, seat) == [held[index] for index in BACKWARDS]


async def test_a_seat_may_not_lay_out_the_hand_of_another(client: AsyncClient) -> None:
    response = await client.post(
        ARRANGEMENTS,
        json=arranging(hand_of(1), BACKWARDS, DEAL, "reach-across"),
        headers=credentials(SORTER),
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["error"] == "ArrangementRefused"


async def test_a_spectator_may_not_arrange_anything(client: AsyncClient) -> None:
    response = await client.post(ARRANGEMENTS, json=sorting(SORTER, DEAL, "first"))

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["error"] == "WrongSeat"


async def test_an_unrecognised_credential_is_turned_away(client: AsyncClient) -> None:
    response = await client.post(
        ARRANGEMENTS,
        json=sorting(SORTER, DEAL, "first"),
        headers={SEAT_HEADER: "picked-up-somewhere"},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["error"] == "Unauthenticated"


async def test_an_order_built_on_a_superseded_position_is_refused(client: AsyncClient) -> None:
    await client.post(MOVES, json=sealing(1, DEAL, "sealed"), headers=credentials(1))

    response = await client.post(ARRANGEMENTS, json=sorting(SORTER, DEAL, "stale"), headers=credentials(SORTER))

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["error"] == "StalePosition"


async def test_an_arrangement_is_admitted_from_a_seat_that_has_already_acted(client: AsyncClient) -> None:
    """A player sorts what it holds while the rest of the table acts, which no turn stands in the way of."""
    await client.post(MOVES, json=sealing(SORTER, DEAL, "sealed"), headers=credentials(SORTER))

    response = await client.post(
        ARRANGEMENTS,
        json=arranging(hand_of(SORTER), tuple(reversed(range(HAND_SIZE - 1))), LANDED, "sort"),
        headers=credentials(SORTER),
    )

    assert response.status_code == HTTPStatus.OK


async def test_an_arrangement_tells_the_other_seats_nothing(client: AsyncClient, session: InService) -> None:
    """A run of placeholders reads the same however it is permuted, so the commit carries no change for them."""
    await client.post(ARRANGEMENTS, json=sorting(SORTER, DEAL, "first"), headers=credentials(SORTER))

    for observer in [seat for seat in range(SEATS) if seat != SORTER] + [None]:
        assert [event.changes for event in session.events(observer, DEAL)] == [()]


async def test_an_arrangement_carries_the_new_order_to_the_seat_that_asked(
    client: AsyncClient, session: InService
) -> None:
    await client.post(ARRANGEMENTS, json=sorting(SORTER, DEAL, "first"), headers=credentials(SORTER))

    (event,) = session.events(SORTER, DEAL)

    assert [change.zone for change in event.changes] == [hand_of(SORTER)]


async def test_a_retried_order_is_answered_with_the_sequence_it_first_reached(client: AsyncClient) -> None:
    retried = sorting(SORTER, DEAL, "the-same-attempt")
    first = await client.post(ARRANGEMENTS, json=retried, headers=credentials(SORTER))

    again = await client.post(ARRANGEMENTS, json=retried, headers=credentials(SORTER))

    assert again.status_code == HTTPStatus.OK
    assert again.json() == first.json()


async def test_a_retried_order_lands_once(client: AsyncClient, session: InService) -> None:
    retried = sorting(SORTER, DEAL, "the-same-attempt")

    await client.post(ARRANGEMENTS, json=retried, headers=credentials(SORTER))
    await client.post(ARRANGEMENTS, json=retried, headers=credentials(SORTER))

    assert session.head == LANDED


async def test_a_refused_arrangement_leaves_the_table_where_it_stood(client: AsyncClient, session: InService) -> None:
    await client.post(
        ARRANGEMENTS,
        json=arranging("draw", (1, 0), DEAL, "the-stock"),
        headers=credentials(SORTER),
    )

    assert session.head == DEAL


@dataclass(frozen=True)
class RefusalCase:
    name: str
    zone: ZoneId
    order: Order


REFUSAL_CASES: Final[tuple[RefusalCase, ...]] = (
    RefusalCase(name="a pile whose run the table keeps", zone="draw", order=(1, 0)),
    RefusalCase(name="a discard read by the card on top of it", zone="discard", order=()),
    RefusalCase(name="a tray whose run records the order the commitments came in", zone=tray_of(SORTER), order=()),
    RefusalCase(name="a zone this table holds none of", zone="nowhere", order=(0,)),
    RefusalCase(name="an order leaving cards of the hand unplaced", zone=hand_of(SORTER), order=(1, 0)),
    RefusalCase(name="an order naming one position twice", zone=hand_of(SORTER), order=(0, 1, 1)),
    RefusalCase(name="an order reaching past the hand", zone=hand_of(SORTER), order=(0, 1, HAND_SIZE)),
)


@pytest.mark.parametrize("case", REFUSAL_CASES, ids=lambda case: case.name)
async def test_an_arrangement_a_seat_holds_no_standing_for_is_refused(client: AsyncClient, case: RefusalCase) -> None:
    response = await client.post(
        ARRANGEMENTS,
        json=arranging(case.zone, case.order, DEAL, "asking"),
        headers=credentials(SORTER),
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["error"] == "ArrangementRefused"


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"order": [0], "base_seq": DEAL, "idempotency_key": "x"}, id="a command naming no zone"),
        pytest.param({"zone": hand_of(SORTER), "base_seq": DEAL, "idempotency_key": "x"}, id="one naming no order"),
        pytest.param(
            {"zone": hand_of(SORTER), "order": [-1, 0, 1], "base_seq": DEAL, "idempotency_key": "x"},
            id="an order naming a position no zone holds",
        ),
        pytest.param(
            {**sorting(SORTER, DEAL, "first"), "seat": 1},
            id="a command naming the seat the credential answers for",
        ),
    ],
)
async def test_an_arrangement_the_schema_rejects_is_refused(client: AsyncClient, body: dict[str, object]) -> None:
    response = await client.post(ARRANGEMENTS, json=body, headers=credentials(SORTER))

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
