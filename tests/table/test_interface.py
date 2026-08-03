from http import HTTPStatus
from pathlib import Path
from typing import Final

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from cardtable.catalogue import GameName
from cardtable.interface import serve_interface

from .tables import BASE_URL, LAYOUT, playing

PAGE: Final[str] = "<!doctype html><title>CardWork</title>"
BUILD: Final[str] = "dist"
ROOT: Final[str] = "/"


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


async def test_a_table_answers_its_own_endpoints_ahead_of_the_page(tmp_path: Path) -> None:
    async with playing(GameName.PASSING) as (client, hosted):
        serve_interface(hosted.app, a_build(tmp_path))

        answered = await client.get(LAYOUT)
        page = await client.get(ROOT)

    assert answered.status_code == HTTPStatus.OK
    assert page.text == PAGE
