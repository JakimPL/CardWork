from collections.abc import AsyncIterator
from http import HTTPStatus
from typing import Final

import pytest
from httpx import ASGITransport, AsyncClient

from cardserver.app import create_app
from cardserver.errors import NoCreation, TablesFull, Unauthorized
from cardserver.identity import ADMIN_HEADER
from cardserver.oversight import Creation, LobbySetting, Oversight, Posting, TokenAdmin
from cardserver.schemas import Founding

from ..games.demo import SEATS
from .company import STREAM_PATIENCE, SWEEP_SECONDS, Gathered, a_sealed_round
from .conftest import BASE_URL, TABLE

COMPANY: Final[tuple[str, ...]] = ("Ada", "Grace", "Alan")
SECRET: Final[str] = "a-hand-of-random-bytes"
ANOTHER: Final[str] = "another-table"
A_SMALLER_TABLE: Final[int] = 2
LONG_ENOUGH: Final[float] = 100_000.0
OPENING: Final[dict[str, object]] = {
    "democratic": True,
    "creation": Creation.SELF_SERVE,
    "stale_seconds": 900.0,
    "idle_seconds": 3600.0,
}


def a_founding(table: str) -> Founding:
    """A guest founding a table of the demo game seating a small company."""
    return Founding(table=table, name="Ada", choice=a_sealed_round(A_SMALLER_TABLE))


def oversight_of(gathered: Gathered, **terms: object) -> Oversight:
    """An overseer over the gathering under test, reading the clock the rest of it reads."""
    return Oversight(
        gathered.gatherings,
        gathered.registry,
        TokenAdmin(SECRET),
        gathered.ticking,
        **{**OPENING, **terms},  # type: ignore[arg-type]
    )


def a_dealt_table(gathered: Gathered) -> dict[str, str]:
    """The table under test dealt into service, and the token each of the company plays through.

    The tokens are what a sweep is weighed against: they are minted at the room and go on to hold the seats of
    the table it became, so a room cleared away is a company turned away from a game still in service.
    """
    gathering = gathered.gathering
    tokens = {name: gathering.admit(name) for name in COMPANY}
    for seat, name in enumerate(COMPANY):
        gathering.claim(name, seat, gathering.revision)

    for name in COMPANY:
        gathering.ready(name, True, gathering.revision)

    gathering.deal(gathering.revision)
    return tokens


def test_a_token_admits_only_the_overseer() -> None:
    admin = TokenAdmin(SECRET)

    admin.confirm(SECRET)

    with pytest.raises(Unauthorized):
        admin.confirm(None)

    with pytest.raises(Unauthorized):
        admin.confirm("picked-up-somewhere")


def test_a_self_serve_lobby_lets_a_guest_found_a_table(gathered: Gathered) -> None:
    oversight = oversight_of(gathered, creation=Creation.SELF_SERVE)

    admitted = oversight.found(a_founding(ANOTHER))

    assert admitted.token
    assert ANOTHER in dict(gathered.gatherings.tables())


def test_a_guarded_lobby_keeps_the_founding_of_tables_to_its_overseer(gathered: Gathered) -> None:
    oversight = oversight_of(gathered, creation=Creation.ADMIN_ONLY)

    with pytest.raises(NoCreation):
        oversight.found(a_founding(ANOTHER))


def test_a_full_lobby_gathers_no_more_tables(gathered: Gathered) -> None:
    oversight = oversight_of(gathered, creation=Creation.SELF_SERVE, capacity=1)

    with pytest.raises(TablesFull):
        oversight.found(a_founding(ANOTHER))


def test_the_overseer_gathers_a_table_holding_no_seat_at_it(gathered: Gathered) -> None:
    oversight = oversight_of(gathered)

    card = oversight.post(Posting(table=ANOTHER, choice=a_sealed_round(A_SMALLER_TABLE)))

    assert card.code is not None
    assert card.host is None
    assert card.phase == "gathering"


async def test_the_overseer_breaks_a_table_in_play_up(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    oversight = oversight_of(gathered)

    await oversight.close(TABLE, "closing up")

    assert TABLE not in dict(gathered.registry.sessions())


def test_the_overseer_reads_the_whole_lobby(gathered: Gathered) -> None:
    oversight = oversight_of(gathered, capacity=8)

    lobby = oversight.lobby()

    assert [card.table for card in lobby.tables] == [TABLE]
    assert lobby.capacity == 8
    assert lobby.census == 1


def test_the_overseer_settles_the_terms_the_lobby_is_held_under(gathered: Gathered) -> None:
    oversight = oversight_of(gathered, creation=Creation.SELF_SERVE, capacity=4)

    settled = oversight.adjust(LobbySetting(capacity=2, creation=Creation.ADMIN_ONLY))

    assert settled.capacity == 2
    assert settled.creation is Creation.ADMIN_ONLY


async def test_a_stale_gathering_is_cleared_away(gathered: Gathered) -> None:
    oversight = oversight_of(gathered, stale_seconds=LONG_ENOUGH)
    gathered.ticking.on(LONG_ENOUGH + 1.0)

    cleared = await oversight.reap()

    assert TABLE in cleared
    assert TABLE not in dict(gathered.gatherings.tables())


async def test_an_idle_table_in_play_is_cleared_away(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    oversight = oversight_of(gathered, stale_seconds=LONG_ENOUGH, idle_seconds=LONG_ENOUGH)
    gathered.ticking.on(LONG_ENOUGH + 1.0)

    cleared = await oversight.reap()

    assert TABLE in cleared
    assert TABLE not in dict(gathered.registry.sessions())


async def test_a_dealt_room_stands_for_as_long_as_the_table_it_became(gathered: Gathered) -> None:
    """A room is read stale by two marks a dealt room always shows, so the deal is what takes it out of reach."""
    a_dealt_table(gathered)
    oversight = oversight_of(gathered, stale_seconds=LONG_ENOUGH, idle_seconds=LONG_ENOUGH * 2)
    gathered.ticking.on(LONG_ENOUGH + 1.0)

    cleared = await oversight.reap()

    assert gathered.gathering.present == 0
    assert TABLE not in cleared
    assert TABLE in dict(gathered.gatherings.tables())


async def test_a_token_minted_before_the_deal_holds_its_seat_through_a_sweep(gathered: Gathered) -> None:
    """The whole of what the room being cleared cost: every seat of a game still in service turned away from it."""
    tokens = a_dealt_table(gathered)
    oversight = oversight_of(gathered, stale_seconds=LONG_ENOUGH, idle_seconds=LONG_ENOUGH * 2)
    gathered.ticking.on(LONG_ENOUGH + 1.0)

    await oversight.reap()

    assert gathered.gatherings.seat(TABLE, tokens["Ada"]) == 0


async def test_a_table_cleared_away_takes_the_room_it_was_played_through_with_it(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    oversight = oversight_of(gathered, stale_seconds=LONG_ENOUGH, idle_seconds=LONG_ENOUGH)
    gathered.ticking.on(LONG_ENOUGH + 1.0)

    await oversight.reap()

    assert TABLE not in dict(gathered.registry.sessions())
    assert TABLE not in dict(gathered.gatherings.tables())


async def test_the_overseer_breaking_a_table_up_clears_the_room_it_was_played_through(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    oversight = oversight_of(gathered)

    await oversight.close(TABLE, "closing up")

    assert TABLE not in dict(gathered.gatherings.tables())


async def test_the_table_this_run_gathers_under_is_left_standing(gathered: Gathered) -> None:
    """The address the run announced, which a lobby standing empty all afternoon is still the lobby of."""
    oversight = oversight_of(gathered, stale_seconds=LONG_ENOUGH, abiding=TABLE)
    gathered.ticking.on(LONG_ENOUGH + 1.0)

    cleared = await oversight.reap()

    assert cleared == ()
    assert gathered.gatherings.gathering() == (TABLE,)


@pytest.fixture(name="overseen")
async def overseen_fixture(gathered: Gathered) -> AsyncIterator[AsyncClient]:
    oversight = oversight_of(gathered, capacity=8)
    app = create_app(
        gathered.registry,
        gathered.gatherings,
        gathered.gatherings,
        oversight,
        sweep_seconds=SWEEP_SECONDS,
        stream_patience=STREAM_PATIENCE,
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        yield client


async def test_the_panel_answers_only_to_the_host_s_token(overseen: AsyncClient) -> None:
    turned_away = await overseen.get("/admin/lobby")
    admitted = await overseen.get("/admin/lobby", headers={ADMIN_HEADER: SECRET})

    assert turned_away.status_code == HTTPStatus.UNAUTHORIZED
    assert admitted.status_code == HTTPStatus.OK
    assert [card["table"] for card in admitted.json()["tables"]] == [TABLE]


async def test_a_guest_founds_a_table_over_the_open_route(overseen: AsyncClient) -> None:
    admitted = await overseen.post(
        "/tables",
        json=a_founding(ANOTHER).model_dump(mode="json"),
    )

    assert admitted.status_code == HTTPStatus.OK
    assert admitted.json()["token"]
    assert admitted.json()["gathering"]["company"][0]["host"] is True


async def test_founding_a_table_under_a_name_already_gathering_is_refused(overseen: AsyncClient) -> None:
    """The name the table under test gathers on is taken, so founding another on it is a refusal, not a fault."""
    refused = await overseen.post(
        "/tables",
        json=a_founding(TABLE).model_dump(mode="json"),
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json()["error"] == "TableTaken"
