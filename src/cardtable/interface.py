from pathlib import Path
from typing import Final

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT: Final[str] = "/"
MOUNT: Final[str] = "interface"


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
