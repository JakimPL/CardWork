from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from typing import Final

import uvicorn

from cardtable.catalogue import GameName, opened
from cardtable.hosting import Hosted
from cardtable.paths import INTERFACE
from cardtable.settings import Settings

PROGRAM: Final[str] = "cardtable"
DESCRIPTION: Final[str] = "Open one table of a CardWork game for local play."

TABLE: Final[str] = "green-baize"
PLAYERS: Final[int] = 3
ROUNDS: Final[int] = 3
SEED: Final[int] = 20260803
GRACE_SECONDS: Final[float] = 2.0
HOST: Final[str] = "127.0.0.1"
PORT: Final[int] = 8000
LOG_LEVEL: Final[str] = "info"


def parser() -> ArgumentParser:
    """The arguments a table is opened with, each standing at something playable until it is given."""
    arguments = ArgumentParser(prog=PROGRAM, description=DESCRIPTION)
    arguments.add_argument(
        "--game",
        choices=tuple(name.value for name in GameName),
        default=GameName.PASSING.value,
        help="which game the table plays",
    )
    arguments.add_argument("--players", type=int, default=PLAYERS, help="how many seats the table holds")
    arguments.add_argument("--rounds", type=int, default=ROUNDS, help="how many rounds a match of rounds runs")
    arguments.add_argument("--seed", type=int, default=SEED, help="the seed every shuffle of the match is drawn from")
    arguments.add_argument("--table", default=TABLE, help="the name the table answers under")
    arguments.add_argument(
        "--grace-seconds",
        type=float,
        default=GRACE_SECONDS,
        help="how long a closed round stays open for a seat to take its commitment back",
    )
    arguments.add_argument("--host", default=HOST, help="the address the server listens on")
    arguments.add_argument("--port", type=int, default=PORT, help="the port the server listens on")
    return arguments


def settings_of(arguments: Namespace) -> Settings:
    """The table a parsed command line asks for, validated as the settings it states.

    Raises:
        ValidationError: when a number given falls outside what a table admits, which is where a seating of
            one or a window of less than nothing is turned away.
    """
    return Settings(
        table=arguments.table,
        players=arguments.players,
        rounds=arguments.rounds,
        seed=arguments.seed,
        grace_seconds=arguments.grace_seconds,
    )


def announcement(hosted: Hosted, host: str, port: int) -> str:
    """The lines a person reads once a table is open: where to point a browser, and as whom.

    A seat is held by whoever offers its token, so one of these lines is the whole of what a player needs,
    and a tab opened holding none watches the table.
    """
    lines = [f"Table {hosted.table!r} is open at http://{host}:{port}"]
    lines.extend(f"  seat {seat}: {token}" for seat, token in sorted(hosted.tokens.items()))
    if hosted.interface is None:
        lines.append(f"  the endpoints answer on their own, since no interface is built at {INTERFACE}")

    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> None:
    """Open one table for local play and answer for it until the process is stopped.

    The table lives as long as the process does, which is why a match runs under no reloader: the position
    a game stands at is held in memory, and a restart deals a fresh one.

    The announcement is flushed as it is written, since the server that follows it holds the process for as
    long as the table lasts and a buffered line would reach a log file after the game rather than before it.
    """
    arguments = parser().parse_args(argv)
    hosted = opened(GameName(arguments.game), settings_of(arguments))
    print(announcement(hosted, arguments.host, arguments.port), flush=True)
    uvicorn.run(hosted.app, host=arguments.host, port=arguments.port, log_level=LOG_LEVEL)
