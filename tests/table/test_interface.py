from http import HTTPStatus
from pathlib import Path
from typing import Final

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from cardtable.games import GameName
from cardtable.interface import TABLE_FIELD, TOKEN_FIELD, joining, serve_interface

from .tables import BASE_URL, LAYOUT, TABLE, playing

DOCTYPE: Final[str] = "<!doctype html>"
PAGE: Final[str] = f"{DOCTYPE}<title>CardWork</title>"
BUILD: Final[str] = "dist"
ROOT: Final[str] = "/"
ADDRESS: Final[str] = "http://127.0.0.1:8000"
TOKEN: Final[str] = "a-token"
SPACED: Final[str] = "green baize"


def a_build(root: Path) -> Path:
    """A directory holding a built page, which is what a run of the interface's own build leaves behind."""
    built = root / BUILD
    built.mkdir()
    (built / "index.html").write_text(PAGE, encoding="utf-8")
    return built


async def test_a_built_interface_is_served_from_the_root(tmp_path: Path) -> None:
    app = FastAPI()

    served = serve_interface(app, a_build(tmp_path))

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.get(ROOT)

    assert served == tmp_path / BUILD
    assert response.text == PAGE


def test_a_checkout_holding_no_build_serves_no_page(tmp_path: Path) -> None:
    assert serve_interface(FastAPI(), tmp_path / BUILD) is None


def test_a_build_that_is_a_file_rather_than_a_directory_serves_no_page(tmp_path: Path) -> None:
    standing_in = tmp_path / BUILD
    standing_in.write_text(PAGE, encoding="utf-8")

    assert serve_interface(FastAPI(), standing_in) is None


def test_the_address_of_a_seat_names_the_table_and_the_token_holding_it() -> None:
    assert joining(ADDRESS, TABLE, TOKEN) == f"{ADDRESS}/#{TABLE_FIELD}={TABLE}&{TOKEN_FIELD}={TOKEN}"


def test_the_address_of_a_tab_watching_a_table_offers_no_token() -> None:
    watching = joining(ADDRESS, TABLE, None)

    assert watching == f"{ADDRESS}/#{TABLE_FIELD}={TABLE}"
    assert TOKEN_FIELD not in watching


def test_a_table_whose_name_holds_a_space_is_named_in_an_address_a_browser_reads() -> None:
    assert joining(ADDRESS, SPACED, None) == f"{ADDRESS}/#{TABLE_FIELD}=green+baize"


def test_the_token_stands_in_the_fragment_of_an_address_rather_than_the_part_a_server_reads() -> None:
    """The whole of why a seat is joined through a fragment: a browser sends the server nothing of one.

    A token in a query would reach the endpoints on every request and stand in whatever they log, so the
    interface reads it out of the fragment and offers it in a header from then on.
    """
    reached, held = joining(ADDRESS, TABLE, TOKEN).split("#")

    assert TOKEN not in reached
    assert TOKEN in held


async def test_a_table_answers_its_own_endpoints_ahead_of_the_page(tmp_path: Path) -> None:
    """A page mounted at the root leaves every endpoint of the table matching ahead of it.

    The host serves whichever build its checkout holds, so a table opened where none stands is handed one
    here. Either way the mount goes on after the endpoints, and the table answers for itself.
    """
    async with playing(GameName.PASSING) as (client, hosted):
        served = hosted.interface or serve_interface(hosted.app, a_build(tmp_path))

        answered = await client.get(LAYOUT)
        page = await client.get(ROOT)

    assert served is not None
    assert answered.status_code == HTTPStatus.OK
    assert page.text.startswith(DOCTYPE)
