from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from pathlib import Path
from typing import Final

import uvicorn

from cardtable.artwork import Artwork, PackName
from cardtable.catalogue import opened
from cardtable.config import Configuration
from cardtable.games import GameName
from cardtable.hosting import Hosted
from cardtable.interface import joining
from cardtable.paths import ASSETS, CONFIGURATION, INTERFACE
from cardtable.service import LogLevel, Service
from cardtable.settings import Settings

PROGRAM: Final[str] = "cardtable"
DESCRIPTION: Final[str] = "Open one table of a CardWork game for local play."
NO_PACK: Final[str] = "none"


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
    arguments.add_argument(
        "--pack",
        choices=(*(name.value for name in PackName), NO_PACK),
        help=f"which pack of card artwork the table draws with, and {NO_PACK!r} for the glyphs the page carries",
    )
    arguments.add_argument("--back", help="which back of that pack every face-down card lies under")
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


def a_pack(given: str | None, stated: PackName | None) -> PackName | None:
    """Which artwork a run draws with: the pack its command line names, the glyphs where it names none of
    them, and the configured pack where it names nothing at all."""
    if given is None:
        return stated

    return None if given == NO_PACK else PackName(given)


def an_artwork(stated: Artwork, arguments: Namespace) -> Artwork:
    """The cards a run draws with: the configured pack and back, under whatever its command line states.

    Raises:
        ValidationError: when a run states a back by an empty name, which names no design of any pack.
    """
    return Artwork(
        pack=a_pack(arguments.pack, stated.pack),
        back=chosen(arguments.back, stated.back),
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
        artwork=an_artwork(stated.artwork, arguments),
        service=a_service(stated.service, arguments),
    )


def address(service: Service) -> str:
    """Where the table answers, as a browser reaches it."""
    return f"http://{service.host}:{service.port}"


def drawing(hosted: Hosted, artwork: Artwork) -> str | None:
    """What a run says of the cards it draws, and nothing at all where it draws the glyphs it asked for.

    A pack asked for and a pack in service are two different things, since the artwork is fetched rather
    than committed: a run naming one that has yet to land says where a fetch would have written it.
    """
    if hosted.artwork is not None:
        return f"  drawn from the {artwork.pack} pack, face down under {artwork.back}"

    if artwork.pack is None:
        return None

    return f"  drawn as glyphs, since no {artwork.pack} pack stands at {ASSETS}"


def announcement(hosted: Hosted, settings: Settings, artwork: Artwork, service: Service) -> str:
    """The lines a person reads once a table is open: which address takes which seat, and which watches it.

    A seat is held by whoever opens its own address, so one of these lines is the whole of what a player is
    handed, and the line holding no token watches the table. The seed stands among them because a table left
    to itself draws one: a run reading it back deals this match again.
    """
    reached = address(service)
    lines = [f"Table {hosted.table!r} is open at {reached}", f"  dealt from seed {settings.seed}"]
    drawn = drawing(hosted, artwork)
    if drawn is not None:
        lines.append(drawn)

    lines.extend(
        f"  seat {seat}: {joining(reached, hosted.table, token)}" for seat, token in sorted(hosted.tokens.items())
    )
    lines.append(f"  watching: {joining(reached, hosted.table, None)}")
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
    hosted = opened(configuration.game, configuration.table, configuration.artwork)
    print(
        announcement(hosted, configuration.table, configuration.artwork, configuration.service),
        flush=True,
    )
    uvicorn.run(
        hosted.app,
        host=configuration.service.host,
        port=configuration.service.port,
        log_level=configuration.service.log_level,
    )
