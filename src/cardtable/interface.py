from pathlib import Path
from typing import Final
from urllib.parse import urlencode

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from cardserver.protocol import TableId

ROOT: Final[str] = "/"
MOUNT: Final[str] = "interface"
TABLE_FIELD: Final[str] = "table"
TOKEN_FIELD: Final[str] = "token"


def serve_interface(app: FastAPI, built: Path) -> Path | None:
    """Serve a built player interface from the root of one application, and report where it came from.

    Handing the page out of the same application the table answers on makes the two one origin, so a client
    reaches `/tables/...` with no cross-origin arrangement of any kind and a token stays in a header. The
    mount goes on last, which leaves every endpoint the table answers matching ahead of it.

    Returns:
        The directory being served, and None where a checkout holds no build yet — that table answers its
        endpoints alone, which is what a first run and every test read.
    """
    if not built.is_dir():
        return None

    app.mount(ROOT, StaticFiles(directory=built, html=True), name=MOUNT)
    return built


def joining(address: str, table: TableId, token: str | None) -> str:
    """The address one tab opens at to take a seat of a table, and to watch it where it holds no token.

    The table and the token stand in the fragment of the address, which a browser keeps to itself: the
    interface reads both out of it as it loads and offers the token in a header from then on, so a token
    stands in no address a server writes down. That leaves one line the whole of what a player is handed.

    Args:
        address: where the table answers, as a browser reaches it.
        table: the name the table is in service under.
        token: the token holding a seat there, and None for a tab watching the table.
    """
    stated = {TABLE_FIELD: table} if token is None else {TABLE_FIELD: table, TOKEN_FIELD: token}
    return f"{address}/#{urlencode(stated)}"
