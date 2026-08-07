from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from pathlib import Path
from typing import Final

import uvicorn

from cardserver.codes import read_out
from cardserver.schemas import Choice
from cardtable.artwork import Artwork, PackName
from cardtable.catalogue import opened
from cardtable.config import Configuration
from cardtable.games import GAMES_HELD
from cardtable.hosting import Hosted
from cardtable.interface import joining
from cardtable.paths import ASSETS, CONFIGURATION, INTERFACE
from cardtable.reaching import a_local_address, reached_at
from cardtable.service import LogLevel, Service
from cardtable.settings import Settings
from cardwork.rounds.conclusion import Conclusion

PROGRAM: Final[str] = "cardtable"
DESCRIPTION: Final[str] = "Gather one table of a CardWork game for local play."
NO_PACK: Final[str] = "none"


def parser() -> ArgumentParser:
    """The file a run is configured from, and every value of it a command line may state instead.

    Each option stands empty until it is given, so an option left alone is one the configuration answers for
    and the file remains the one place a value is read from.
    """
    arguments = ArgumentParser(prog=PROGRAM, description=DESCRIPTION)
    arguments.add_argument(
        "--config",
        type=Path,
        default=CONFIGURATION,
        help="the file the run is configured from",
    )
    arguments.add_argument(
        "--game",
        choices=GAMES_HELD,
        help="which game the table opens on",
    )
    arguments.add_argument(
        "--table",
        help="the name the table answers under",
    )
    arguments.add_argument(
        "--code",
        help="the hand of ranks the gathering admits on",
    )
    arguments.add_argument(
        "--players",
        type=int,
        help="how many seats the table opens on",
    )
    arguments.add_argument(
        "--decks",
        type=int,
        help="how many standard decks the game is dealt from",
    )
    arguments.add_argument(
        "--rounds",
        type=int,
        help="how many rounds the match runs",
    )
    arguments.add_argument(
        "--target",
        type=int,
        help="the score a seat reaches to end the match",
    )
    arguments.add_argument(
        "--lead",
        type=int,
        help="the lead over the next best seat that ends the match",
    )
    arguments.add_argument(
        "--seed",
        type=int,
        help="the seed every shuffle of the match is drawn from",
    )
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
    arguments.add_argument(
        "--back",
        help="which back of that pack every face-down card lies under",
    )
    arguments.add_argument(
        "--host",
        help="the address the server listens on",
    )
    arguments.add_argument(
        "--port",
        type=int,
        help="the port the server listens on",
    )
    arguments.add_argument(
        "--advertise",
        help="the address a guest is handed, where it differs from the one bound",
    )
    arguments.add_argument(
        "--log-level",
        choices=tuple(level.value for level in LogLevel),
        help="how much of what the server does reaches the log",
    )
    return arguments


def chosen[ValueT](given: ValueT | None, stated: ValueT) -> ValueT:
    """The value a run takes: the one its command line gives, or the one its configuration states."""
    return stated if given is None else given


def a_conclusion(stated: Conclusion, arguments: Namespace) -> Conclusion:
    """How long a run's match lasts: the clauses its command line states, or the ones its configuration does.

    A clause named on the command line states the ending whole, so `--rounds 5` runs five rounds of whatever the
    file was configured to run to. Naming a clause beside the configured ones is asked for by stating both.

    Raises:
        ValidationError: when a clause given falls below the least a match runs to.
    """
    given = (arguments.rounds, arguments.target, arguments.lead)
    if all(clause is None for clause in given):
        return stated

    return Conclusion(
        rounds=arguments.rounds,
        target=arguments.target,
        lead=arguments.lead,
    )


def a_table(stated: Settings, arguments: Namespace) -> Settings:
    """The table a run gathers: the configured one, holding every value its command line states instead.

    Raises:
        ValidationError: when a value given falls outside what a table admits, which is where a window of less
            than nothing and a code reading as no hand of ranks are turned away.
    """
    return Settings(
        name=chosen(arguments.table, stated.name),
        code=chosen(arguments.code, stated.code),
        seed=chosen(arguments.seed, stated.seed),
        grace_seconds=chosen(arguments.grace_seconds, stated.grace_seconds),
    )


def a_choice(stated: Choice, arguments: Namespace) -> Choice:
    """What a run's gathering opens on: the configured choice, holding every value its command line states instead.

    Raises:
        ValidationError: when a value given falls outside what any table plays at, which is where a seating of
            nobody and a deal from no deck at all are turned away.
    """
    return Choice(
        game=chosen(arguments.game, stated.game),
        players=chosen(arguments.players, stated.players),
        decks=chosen(arguments.decks, stated.decks),
        conclusion=a_conclusion(stated.conclusion, arguments),
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
    """Where a run answers: the configured address, advertisement and log level, under whatever its command
    line states.

    Raises:
        ValidationError: when a port given lies outside the range a machine listens on.
    """
    return Service(
        host=chosen(arguments.host, stated.host),
        port=chosen(arguments.port, stated.port),
        advertise=chosen(arguments.advertise, stated.advertise),
        log_level=chosen(arguments.log_level, stated.log_level),
    )


def configured(arguments: Namespace) -> Configuration:
    """The run a parsed command line asks for: the file it names, as this run departs from it.

    Raises:
        FileNotFoundError: when no file stands where the run was told to read its configuration from.
        ValidationError: when the file, or the command line reading over it, states a run no table gathers.
    """
    stated = Configuration.read(arguments.config)
    return Configuration(
        table=a_table(stated.table, arguments),
        choice=a_choice(stated.choice, arguments),
        artwork=an_artwork(stated.artwork, arguments),
        service=a_service(stated.service, arguments),
        advanced=stated.advanced,
    )


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


def announcement(
    hosted: Hosted,
    settings: Settings,
    artwork: Artwork,
    reached: Sequence[str],
) -> str:
    """The lines a person reads once a table is gathering: the code it admits on, and where it is reached.

    Any one of these addresses is the whole of what a guest is handed: opening it arrives at the gathering,
    where a person names themselves, takes a seat and settles what is played with everyone else there. The code
    is read out apart as well as carried in the addresses, since a code said across a room is written down by
    hand at the other end.

    The seed stands among them because a table left to itself draws one: a run reading it back deals this match
    again.
    """
    lines = [f"Table {hosted.table!r} is gathering — join code {read_out(hosted.code)}"]
    lines.extend(f"  {joining(address, hosted.table, hosted.code)}" for address in reached)
    lines.append(f"  dealt from seed {settings.seed}")
    drawn = drawing(hosted, artwork)
    if drawn is not None:
        lines.append(drawn)

    if hosted.interface is None:
        lines.append(f"  the endpoints answer on their own, since no interface is built at {INTERFACE}")

    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> None:
    """Gather the table a run is configured for and answer for it until the process is stopped.

    The gathering and the table it becomes live as long as the process does, which is why a match runs under no
    reloader: the company at a table and the position it stands at are held in memory, and a restart gathers a
    fresh one.

    The announcement is flushed as it is written, since the server that follows it holds the process for as
    long as the table lasts and a buffered line would reach a log file after the game rather than before it.
    """
    configuration = configured(parser().parse_args(argv))
    hosted = opened(
        configuration.table,
        configuration.choice,
        configuration.artwork,
        configuration.advanced,
    )
    print(
        announcement(
            hosted,
            configuration.table,
            configuration.artwork,
            reached_at(configuration.service, a_local_address),
        ),
        flush=True,
    )
    uvicorn.run(
        hosted.app,
        host=configuration.service.host,
        port=configuration.service.port,
        log_level=configuration.service.log_level,
    )
