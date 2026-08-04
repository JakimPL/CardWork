from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from cardserver.app import create_app
from cardserver.identity import TokenSeats
from cardserver.protocol import Presentation, Table, TableId
from cardserver.registry import TableRegistry
from cardtable.artwork import Artwork, serve_artwork
from cardtable.interface import serve_interface
from cardtable.paths import ASSETS, INTERFACE
from cardtable.seats import tokens_for
from cardtable.settings import Settings
from cardwork.states.state import GameState


@dataclass(frozen=True)
class Hosted:
    """One table in service: the application answering for it, and what a person needs to reach it.

    The state type of the game is settled as the table is opened and stays inside, which is what lets one
    host put games whose cursors are of different shapes into service through the one call.
    """

    app: FastAPI
    table: TableId
    tokens: Mapping[int, str]
    artwork: Path | None
    interface: Path | None


def serve[StateT: GameState](
    table: Table[StateT],
    presentation: Presentation,
    settings: Settings,
    artwork: Artwork,
) -> Hosted:
    """Put one table into service: the game, the arrangement it is read through, and a token for each seat.

    Everything a player interface needs answers from the single application this builds — the endpoints of
    the table under `/tables`, the cards it draws with under `/artwork` where a pack has been fetched, and
    the page itself at the root where a build of it exists. The artwork goes on ahead of the page, since the
    page is mounted at the root and everything answering for itself is registered before it.
    """
    registry = TableRegistry[StateT](settings.grace_seconds)
    registry.open(settings.name, table, presentation)
    tokens = tokens_for(table.players)
    seats = TokenSeats({settings.name: {token: seat for seat, token in tokens.items()}})
    app = create_app(registry, seats)
    return Hosted(
        app=app,
        table=settings.name,
        tokens=tokens,
        artwork=serve_artwork(app, ASSETS, artwork),
        interface=serve_interface(app, INTERFACE),
    )
