from argparse import ArgumentParser
from collections.abc import Mapping, Sequence
from json import dumps
from pathlib import Path
from time import monotonic
from typing import Final

from cardserver.app import create_app
from cardserver.gathering import Gatherings, GovernedSay, Turnstile
from cardserver.registry import TableRegistry
from cardtable.catalogue import OFFERINGS, Deals
from cardtable.paths import SPECIFICATION

NO_GRACE: Final[float] = 0.0
NO_SEED: Final[int] = 0
INDENT: Final[int] = 2
TURNSTILE_WINDOW: Final[float] = 60.0
WRONG_CODES_ALLOWED: Final[int] = 10
SWEEP_SECONDS: Final[float] = 60.0

Document = Mapping[str, object]


def document() -> Document:
    """The OpenAPI document of the protocol a table answers, read off an application gathering no table.

    A schema follows from the endpoints rather than from any position, so this builds the application with an
    empty registry and a lobby nobody has arrived at: what a client sends and what it is answered stands the
    same whichever game is in service. The lobby is the host's own, since the endpoints a table is gathered at
    answer only where one is held.
    """
    registry = TableRegistry(NO_GRACE)
    gatherings = Gatherings(
        Deals(registry, NO_SEED),
        offerings=OFFERINGS,
        say=GovernedSay(),
        turnstile=Turnstile.watching(
            monotonic,
            window=TURNSTILE_WINDOW,
            wrong_codes_allowed=WRONG_CODES_ALLOWED,
        ),
        clock=monotonic,
    )
    return create_app(registry, gatherings, gatherings, sweep_seconds=SWEEP_SECONDS).openapi()


def write(specification: Document, into: Path) -> int:
    """Write one document where the interface generates its types from, and answer with how many bytes landed."""
    body = (
        dumps(
            specification,
            indent=INDENT,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    )
    into.parent.mkdir(parents=True, exist_ok=True)
    into.write_text(body, encoding="utf-8")
    return len(body)


def parser() -> ArgumentParser:
    """Where the document lands, which stands at the file the interface generates from until it is given."""
    arguments = ArgumentParser(
        prog="openapi",
        description="Write the OpenAPI document of a table, which the player interface types are generated from.",
    )
    arguments.add_argument(
        "--into",
        type=Path,
        default=SPECIFICATION,
        help="the file the document is written to",
    )
    return arguments


def main(argv: Sequence[str] | None = None) -> None:
    """Write the document and say where it landed, so a person reads the same path the generator is handed."""
    into = Path(parser().parse_args(argv).into)
    print(f"{into}: {write(document(), into)} bytes")


if __name__ == "__main__":
    main()
