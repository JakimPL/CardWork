from http import HTTPStatus
from typing import Final

import pytest
from httpx import HTTPStatusError

from cardtable.catalogue import opened
from cardtable.games import GameName

from .config import ADMIN, ADVANCED, GLYPHS, NOTHING_KEPT
from .tables import (
    CHOICE,
    GATHERING,
    SETTINGS,
    UNSERVED,
    a_dealt_table,
    arrives,
    gathering,
    playing,
)

A_SEAT: Final[int] = 0
ANOTHER_NAME: Final[str] = "Turing"
ONE_SEAT_SHORT: Final[int] = CHOICE.players - 1


async def test_a_table_answers_under_the_name_it_was_gathered_under() -> None:
    async with playing(GameName.PASSING) as dealt:
        response = await dealt.client.get(f"/tables/{dealt.hosted.table}/layout")

    assert response.status_code == HTTPStatus.OK


async def test_a_name_no_table_was_gathered_under_answers_for_none() -> None:
    async with playing(GameName.PASSING) as dealt:
        response = await dealt.client.get(f"/tables/{UNSERVED}/layout")

    assert response.status_code == HTTPStatus.NOT_FOUND


async def test_a_gathering_and_the_table_it_becomes_answer_at_the_one_address() -> None:
    """Both halves of a run stand behind one name, which is what lets a person be handed a single line."""
    async with playing(GameName.PASSING) as dealt:
        room = await dealt.client.get(GATHERING, headers=dealt.credentials(A_SEAT))
        table = await dealt.client.get(f"/tables/{dealt.hosted.table}/layout")

    assert room.json()["dealt"] is True
    assert table.status_code == HTTPStatus.OK


async def test_a_table_stands_in_service_nowhere_until_its_company_deals_it() -> None:
    """What a gathering stands in place of: the cards are dealt when the company says so and not before."""
    async with gathering(CHOICE) as (client, hosted):
        answered = await client.get(f"/tables/{hosted.table}/layout")

    assert answered.status_code == HTTPStatus.NOT_FOUND


def test_a_hosted_table_hands_out_the_code_it_gathers_behind() -> None:
    assert opened(SETTINGS, CHOICE, GLYPHS, ADVANCED, ADMIN, records=NOTHING_KEPT).code == SETTINGS.code


async def test_a_guest_arriving_at_one_table_is_minted_a_token_of_that_gathering_alone() -> None:
    async with playing(GameName.PASSING) as first:
        async with playing(GameName.PASSING) as second:
            assert set(first.tokens.values()).isdisjoint(second.tokens.values())


async def test_a_dealt_gathering_admits_nobody_further() -> None:
    async with playing(GameName.PASSING) as dealt:
        with pytest.raises(HTTPStatusError):
            await arrives(dealt.client, dealt.hosted.code, ANOTHER_NAME)


async def test_a_company_leaving_a_seat_empty_deals_no_table() -> None:
    async with gathering(CHOICE) as (client, hosted):
        with pytest.raises(HTTPStatusError):
            await a_dealt_table(client, hosted.code, ONE_SEAT_SHORT)
