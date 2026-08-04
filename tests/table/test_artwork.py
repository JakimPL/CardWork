from http import HTTPStatus
from pathlib import Path
from typing import Final

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from cardtable.artwork import ARTWORK, MANIFEST, Artwork, PackManifest, PackName, ServedPack, serve_artwork

from .tables import BASE_URL

CROSSHATCH: Final[str] = "crosshatch"
ROBOT: Final[str] = "robot"
UNDRAWN: Final[str] = "tartan"
CARD: Final[str] = "ace_of_spades.png"
PICTURE: Final[bytes] = b"the ace of spades as a hand placed it"

FETCHED: Final[PackManifest] = PackManifest(
    pack=PackName.KARE,
    extension="png",
    width=284,
    height=384,
    pixelated=True,
    cornered=True,
    backs=(CROSSHATCH, ROBOT),
)

DRAWING: Final[Artwork] = Artwork(pack=PackName.KARE, back=ROBOT)
GLYPHS: Final[Artwork] = Artwork(pack=None, back=ROBOT)


def a_fetched_pack(root: Path, manifest: PackManifest) -> Path:
    """A pack standing on disk as a fetch leaves one: a picture per card, and what the pack states of itself."""
    pack = root / manifest.pack
    pack.mkdir(parents=True)
    (pack / CARD).write_bytes(PICTURE)
    (pack / MANIFEST).write_text(manifest.model_dump_json(), encoding="utf-8")
    return pack


def a_table_drawing(root: Path, artwork: Artwork) -> tuple[FastAPI, Path | None]:
    """One application serving whatever artwork a run asks of it, beside where that artwork came from."""
    app = FastAPI()
    return app, serve_artwork(app, root, artwork)


async def read(app: FastAPI, path: str) -> tuple[HTTPStatus, bytes]:
    """What one application answers at an address, as a page reaching it reads the answer."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.get(path)

    return HTTPStatus(response.status_code), response.content


async def test_a_fetched_pack_hands_out_the_card_a_page_asks_for(tmp_path: Path) -> None:
    a_fetched_pack(tmp_path, FETCHED)
    app, served = a_table_drawing(tmp_path, DRAWING)

    status, drawn = await read(app, f"{ARTWORK}/{CARD}")

    assert served == tmp_path / PackName.KARE
    assert status == HTTPStatus.OK
    assert drawn == PICTURE


async def test_the_pack_states_itself_at_one_address_and_names_the_back_this_table_chose(tmp_path: Path) -> None:
    """What a page is told as it opens: the pack's own account of itself, and the back this run asked for.

    The route answers ahead of the file of the same name lying in the pack, which is the whole reason the
    back reaches a page at all: the pack states which backs it holds, and the table states which it draws.
    """
    a_fetched_pack(tmp_path, FETCHED)
    app, _ = a_table_drawing(tmp_path, DRAWING)

    status, stated = await read(app, f"{ARTWORK}/{MANIFEST}")

    assert status == HTTPStatus.OK
    assert ServedPack.model_validate_json(stated) == ServedPack.drawing(FETCHED, ROBOT)


def test_a_run_asking_for_no_pack_serves_none(tmp_path: Path) -> None:
    a_fetched_pack(tmp_path, FETCHED)

    assert a_table_drawing(tmp_path, GLYPHS)[1] is None


def test_a_checkout_that_has_fetched_nothing_serves_no_pack(tmp_path: Path) -> None:
    """A pack is fetched rather than committed, so a table opens whether or not one landed."""
    assert a_table_drawing(tmp_path, DRAWING)[1] is None


def test_a_directory_holding_no_manifest_stands_for_no_pack(tmp_path: Path) -> None:
    (tmp_path / PackName.KARE).mkdir()

    assert a_table_drawing(tmp_path, DRAWING)[1] is None


def test_a_back_the_pack_that_landed_holds_no_design_for_is_turned_away(tmp_path: Path) -> None:
    """The artwork is there and the run asks for something else in it, which is worth refusing outright."""
    a_fetched_pack(tmp_path, FETCHED)

    with pytest.raises(ValidationError):
        a_table_drawing(tmp_path, Artwork(pack=PackName.KARE, back=UNDRAWN))


async def test_a_pack_serves_the_pictures_of_its_own_directory_and_nothing_beside_them(tmp_path: Path) -> None:
    """A fetch keeps the sources it cuts a pack from beside the packs, so what a table serves is pictures."""
    a_fetched_pack(tmp_path, FETCHED)
    (tmp_path / ".sources").mkdir()
    (tmp_path / ".sources" / "cards.dll").write_bytes(PICTURE)
    app, _ = a_table_drawing(tmp_path, DRAWING)

    status, _ = await read(app, f"{ARTWORK}/.sources/cards.dll")

    assert status == HTTPStatus.NOT_FOUND
