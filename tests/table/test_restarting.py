import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus
from json import dumps, loads
from os import utime
from pathlib import Path
from time import time
from typing import Final

import pytest
from httpx import AsyncClient

from cardserver.identity import SEAT_HEADER
from cardtable.catalogue import SECONDS_AN_HOUR, opened
from cardtable.hosting import Hosted
from cardtable.records import a_directory_name
from cardtable.records.naming import ORIGIN_FILE, ROOM_FILE, SET_ASIDE
from cardtable.records.writing import ENCODING
from cardtable.settings import Settings
from cardwork.presentation.layout import Layout

from .config import ADMIN, ADVANCED, CODE, GLYPHS, NOTHING_KEPT, RETAIN_HOURS, kept_at
from .tables import (
    CHOICE,
    GATHERING,
    LAYOUT,
    NAMES,
    NO_GRACE,
    PLAYERS,
    SEED,
    TABLE,
    VIEW,
    Dealt,
    a_dealt_table,
    a_seat_to_act,
    arrives,
    serving,
    submit,
)

A_SEAT: Final[int] = 0
A_MOMENT: Final[float] = 1.0
ANOTHER_SEED: Final[int] = SEED + 1
NO_SUCH_GAME: Final[str] = "bridge"


def a_drawn_run() -> Settings:
    """The settings one run of the host starts under, drawing a code and a seed of its own.

    A restart states neither, which is what makes an assertion here say something: the room a company reaches
    and the position they left their table at both come off the record rather than off anything this run was
    handed.
    """
    return Settings(name=TABLE, grace_seconds=NO_GRACE)


@asynccontextmanager
async def a_run(store: Path, settings: Settings) -> AsyncIterator[tuple[AsyncClient, Hosted]]:
    """One run of the host over a store of its own, letting go of that store as it ends.

    A store is one run's to write, so a run lets go before the next takes it up. A process ending is what
    usually says so, and this is what says it where two runs stand one after the other inside one process.
    """
    hosted = opened(settings, CHOICE, GLYPHS, ADVANCED, ADMIN, records=kept_at(store))
    try:
        async with serving(hosted) as client:
            yield client, hosted
    finally:
        hosted.keeping.close()


def credentials(token: str) -> dict[str, str]:
    """The header one seat of a table speaks through, which is the token its guest arrived under."""
    return {SEAT_HEADER: token}


def opening_a_loop_of_its_own(*_arguments: object, **_keywords: object) -> None:
    """What stands in for opening a loop, so a run reaching for one is read here rather than in a page that hangs.

    Raises:
        AssertionError: whenever it is called at all, which is the whole of what it is here to say.
    """
    raise AssertionError("A run reads its lobby back inside the loop that serves it, and this one opened its own")


async def a_played_table(client: AsyncClient, hosted: Hosted) -> Dealt:
    """One table gathered, seated, dealt and moved on by a seat, as a company reaching the host leaves it."""
    dealt = Dealt(
        client=client,
        hosted=hosted,
        tokens=await a_dealt_table(client, hosted.code, PLAYERS),
    )
    seat, move, base_seq = await a_seat_to_act(dealt)
    await submit(dealt, seat, move, base_seq)
    return dealt


async def test_every_seat_plays_on_through_the_token_it_arrived_under(tmp_path: Path) -> None:
    """The whole of what a restart is asked for: the address in a page's own bar reopens the seat it held."""
    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        tokens = (await a_played_table(client, hosted)).tokens

    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        served = [
            (await client.get(VIEW, headers=credentials(tokens[seat]))).json()["observer"] for seat in range(PLAYERS)
        ]

    assert served == list(range(PLAYERS))


async def test_a_table_stands_where_the_company_left_it(tmp_path: Path) -> None:
    """The cards a seat holds, the sequence the table stands at and the moves it is offered, all as they were."""
    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        tokens = (await a_played_table(client, hosted)).tokens
        before = (await client.get(VIEW, headers=credentials(tokens[A_SEAT]))).json()

    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        after = (await client.get(VIEW, headers=credentials(tokens[A_SEAT]))).json()

    assert after == before


async def test_a_move_built_before_the_restart_lands_after_it(tmp_path: Path) -> None:
    """A move is pinned to the sequence it was built on, so one landing says the table stands at that sequence."""
    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        dealt = Dealt(
            client=client,
            hosted=hosted,
            tokens=await a_dealt_table(client, hosted.code, PLAYERS),
        )
        seat, move, base_seq = await a_seat_to_act(dealt)

    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        status = await submit(Dealt(client=client, hosted=hosted, tokens=dealt.tokens), seat, move, base_seq)

    assert status == HTTPStatus.OK


async def test_the_layout_carries_the_names_the_company_settled(tmp_path: Path) -> None:
    """The plaques are settled at the deal, so a table taken up is read by the names its gathering left on it."""
    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        tokens = (await a_played_table(client, hosted)).tokens

    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        response = await client.get(LAYOUT, headers=credentials(tokens[A_SEAT]))

    plaques = Layout.model_validate(response.json()).plaques
    assert tuple(plaque.name for plaque in plaques) == NAMES[:PLAYERS]


async def test_a_table_is_read_back_whatever_seed_the_run_was_dealt_from(tmp_path: Path) -> None:
    """A seed deals a table and a record is what one taken up stands on, so the two never meet."""
    dealt_from = Settings(name=TABLE, code=CODE, seed=SEED, grace_seconds=NO_GRACE)
    dealt_from_another = Settings(name=TABLE, code=CODE, seed=ANOTHER_SEED, grace_seconds=NO_GRACE)

    async with a_run(tmp_path, dealt_from) as (client, hosted):
        tokens = (await a_played_table(client, hosted)).tokens
        before = (await client.get(VIEW, headers=credentials(tokens[A_SEAT]))).json()

    async with a_run(tmp_path, dealt_from_another) as (client, hosted):
        after = (await client.get(VIEW, headers=credentials(tokens[A_SEAT]))).json()

    assert after == before


async def test_the_run_announces_the_code_the_room_it_read_back_admits_on(tmp_path: Path) -> None:
    """A run drawing a fresh code would announce one that admits nobody at the room its company is standing in."""
    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        announced = hosted.code
        await arrives(client, announced, NAMES[A_SEAT])

    async with a_run(tmp_path, a_drawn_run()) as (client, restarted):
        arriving = await arrives(client, restarted.code, NAMES[A_SEAT + 1])

    assert restarted.code == announced
    assert arriving.gathering.table == TABLE


async def test_a_company_still_settling_what_to_play_comes_back_to_the_room_they_were_in(tmp_path: Path) -> None:
    """A run gathering a second room under the name would raise, and take the whole host down as it started."""
    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        admitted = await arrives(client, hosted.code, NAMES[A_SEAT])

    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        response = await client.get(GATHERING, headers=credentials(admitted.token))

    assert response.status_code == HTTPStatus.OK
    assert [guest["name"] for guest in response.json()["company"]] == [NAMES[A_SEAT]]


async def test_a_lobby_is_read_back_inside_the_loop_that_goes_on_to_serve_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A loop opened to read a lobby back would be closed before a client waited on anything built inside it.

    Every stream a table is followed through waits on a condition the session holds, so a table restored under
    a loop of its own leaves each of them waiting on a loop that has ended: the page shows a table that never
    moves and never learns otherwise. Reading a lobby back inside the loop already running is what says none
    was opened, since opening one there is refused outright.
    """
    monkeypatch.setattr(asyncio, "run", opening_a_loop_of_its_own)

    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        tokens = (await a_played_table(client, hosted)).tokens

    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        response = await client.get(VIEW, headers=credentials(tokens[A_SEAT]))

    assert response.status_code == HTTPStatus.OK


async def test_a_run_that_keeps_nothing_gathers_a_lobby_of_its_own(tmp_path: Path) -> None:
    """What a checkout being played with holds: a table that lives as long as the run holding it.

    The layout is read as a spectator reads it, since a table standing nowhere is what this says: a token
    minted at a room another run gathered is turned away for being nobody's here, whatever became of the
    table it once held a seat at.
    """
    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        await a_played_table(client, hosted)

    forgetful = opened(a_drawn_run(), CHOICE, GLYPHS, ADVANCED, ADMIN, records=NOTHING_KEPT)
    async with serving(forgetful) as client:
        response = await client.get(LAYOUT)

    assert response.status_code == HTTPStatus.NOT_FOUND


async def test_a_table_written_down_without_the_room_it_was_gathered_in_is_left_alone(tmp_path: Path) -> None:
    """A room is the whole of identity at a table, so one served without its room turns its own company away."""
    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        await a_played_table(client, hosted)

    (tmp_path / a_directory_name(TABLE) / ROOM_FILE).unlink()

    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        response = await client.get(LAYOUT)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert (tmp_path / f"{a_directory_name(TABLE)}{SET_ASIDE}").is_dir()


async def test_a_record_naming_a_game_this_host_offers_nowhere_is_set_aside(tmp_path: Path) -> None:
    """The record a deployment whose offerings have moved on finds, which the tables beside it outlive."""
    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        await a_played_table(client, hosted)

    written = tmp_path / a_directory_name(TABLE) / ROOM_FILE
    unheld = loads(written.read_text(encoding=ENCODING))
    unheld["choice"]["game"] = NO_SUCH_GAME
    written.write_text(dumps(unheld), encoding=ENCODING)

    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        response = await client.get(LAYOUT)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert (tmp_path / f"{a_directory_name(TABLE)}{SET_ASIDE}").is_dir()


async def test_a_record_nobody_came_back_to_is_cleared_away_as_a_run_starts(tmp_path: Path) -> None:
    """The one moment a store is weighed against a calendar, since every clock a reaper reads starts with a run."""
    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        await a_played_table(client, hosted)

    written = tmp_path / a_directory_name(TABLE)
    long_ago = time() - (RETAIN_HOURS * SECONDS_AN_HOUR + A_MOMENT)
    utime(written / ROOM_FILE, (long_ago, long_ago))

    async with a_run(tmp_path, a_drawn_run()) as (client, hosted):
        response = await client.get(LAYOUT)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert not (written / ORIGIN_FILE).exists()
