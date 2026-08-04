from http import HTTPStatus

from cardtable.catalogue import opened
from cardtable.games import GameName

from .config import GLYPHS
from .tables import PLAYERS, SETTINGS, UNSERVED, playing


async def test_a_table_answers_under_the_name_it_was_opened_with() -> None:
    async with playing(GameName.PASSING) as (client, hosted):
        response = await client.get(f"/tables/{hosted.table}/layout")

    assert response.status_code == HTTPStatus.OK


async def test_a_name_no_table_was_opened_under_answers_for_none() -> None:
    async with playing(GameName.PASSING) as (client, _):
        response = await client.get(f"/tables/{UNSERVED}/layout")

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_a_hosted_table_holds_a_token_for_every_seat_it_seats() -> None:
    hosted = opened(GameName.PASSING, SETTINGS, GLYPHS)

    assert sorted(hosted.tokens) == list(range(PLAYERS))


def test_two_tables_opened_alike_hand_out_tokens_of_their_own() -> None:
    first = opened(GameName.PASSING, SETTINGS, GLYPHS)
    second = opened(GameName.PASSING, SETTINGS, GLYPHS)

    assert set(first.tokens.values()).isdisjoint(second.tokens.values())
