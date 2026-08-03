from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from pathlib import Path
from typing import Final

import uvicorn

from cardtable.catalogue import opened
from cardtable.config import Configuration
from cardtable.games import GameName
from cardtable.hosting import Hosted
from cardtable.paths import CONFIGURATION, INTERFACE
from cardtable.service import LogLevel, Service
from cardtable.settings import Settings

PROGRAM: Final[str] = "cardtable"
DESCRIPTION: Final[str] = "Open one table of a CardWork game for local play."


def parser() -> ArgumentParser:
    """The file a run is configured from, and every value of it a command line may state instead.

    Each option stands empty until it is given, so an option left alone is one the configuration answers for
    and the file remains the one place a value is read from.
    """
    arguments = ArgumentParser(prog=PROGRAM, description=DESCRIPTION)
    arguments.add_argument("--config", type=Path, default=CONFIGURATION, help="the file the run is configured from")
    arguments.add_argument(
        "--game",
        choices=tuple(name.value for name in GameName),
        help="which game the table plays",
    )
    arguments.add_argument("--table", help="the name the table answers under")
    arguments.add_argument("--players", type=int, help="how many seats the table holds")
    arguments.add_argument("--rounds", type=int, help="how many rounds a match of rounds runs")
    arguments.add_argument("--seed", type=int, help="the seed every shuffle of the match is drawn from")
    arguments.add_argument(
        "--grace-seconds",
        type=float,
        help="how long a closed round stays open for a seat to take its commitment back",
    )
    arguments.add_argument("--host", help="the address the server listens on")
    arguments.add_argument("--port", type=int, help="the port the server listens on")
    arguments.add_argument(
        "--log-level",
        choices=tuple(level.value for level in LogLevel),
        help="how much of what the server does reaches the log",
    )
    return arguments


def chosen[ValueT](given: ValueT | None, stated: ValueT) -> ValueT:
    """The value a run takes: the one its command line gives, or the one its configuration states."""
    return stated if given is None else given


def a_table(stated: Settings, arguments: Namespace) -> Settings:
    """The table a run opens: the configured one, holding every value its command line states instead.

    Raises:
        ValidationError: when a value given falls outside what a table admits, which is where a seating of
            one or a window of less than nothing is turned away.
    """
    return Settings(
        name=chosen(arguments.table, stated.name),
        players=chosen(arguments.players, stated.players),
        rounds=chosen(arguments.rounds, stated.rounds),
        seed=chosen(arguments.seed, stated.seed),
        grace_seconds=chosen(arguments.grace_seconds, stated.grace_seconds),
    )


def a_service(stated: Service, arguments: Namespace) -> Service:
    """Where a run answers: the configured address and log level, under whatever its command line states.

    Raises:
        ValidationError: when a port given lies outside the range a machine listens on.
    """
    return Service(
        host=chosen(arguments.host, stated.host),
        port=chosen(arguments.port, stated.port),
        log_level=chosen(arguments.log_level, stated.log_level),
    )


def configured(arguments: Namespace) -> Configuration:
    """The run a parsed command line asks for: the file it names, as this run departs from it.

    Raises:
        FileNotFoundError: when no file stands where the run was told to read its configuration from.
        ValidationError: when the file, or the command line reading over it, states a run no table opens.
    """
    stated = Configuration.read(arguments.config)
    return Configuration(
        game=chosen(arguments.game, stated.game),
        table=a_table(stated.table, arguments),
        service=a_service(stated.service, arguments),
    )


def announcement(hosted: Hosted, service: Service) -> str:
    """The lines a person reads once a table is open: where to point a browser, and as whom.

    A seat is held by whoever offers its token, so one of these lines is the whole of what a player needs,
    and a tab opened holding none watches the table.
    """
    lines = [f"Table {hosted.table!r} is open at http://{service.host}:{service.port}"]
    lines.extend(f"  seat {seat}: {token}" for seat, token in sorted(hosted.tokens.items()))
    if hosted.interface is None:
        lines.append(f"  the endpoints answer on their own, since no interface is built at {INTERFACE}")

    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> None:
    """Open the table a run is configured for and answer for it until the process is stopped.

    The table lives as long as the process does, which is why a match runs under no reloader: the position
    a game stands at is held in memory, and a restart deals a fresh one.

    The announcement is flushed as it is written, since the server that follows it holds the process for as
    long as the table lasts and a buffered line would reach a log file after the game rather than before it.
    """
    configuration = configured(parser().parse_args(argv))
    hosted = opened(configuration.game, configuration.table)
    print(announcement(hosted, configuration.service), flush=True)
    uvicorn.run(
        hosted.app,
        host=configuration.service.host,
        port=configuration.service.port,
        log_level=configuration.service.log_level,
    )
