from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from cardserver.app import create_app
from cardserver.gathering.gatherings import Gatherings
from cardserver.protocols.table import TableId
from cardserver.registry import TableRegistry
from cardserver.schemas.choice import Choice
from cardtable.artwork import Artwork, serve_artwork
from cardtable.interface import serve_interface
from cardtable.paths import ASSETS, INTERFACE
from cardtable.settings import Settings


@dataclass(frozen=True)
class Hosted:
    """One table gathering: the application answering for it, and what a person needs to reach it.

    The code is the whole of what is handed out, since a guest names themselves on arrival and is minted the
    token they play through there. The state type of the game is settled as the table is dealt and stays
    inside, which is what lets one host put games whose cursors are of different shapes into service.
    """

    app: FastAPI
    table: TableId
    code: str
    artwork: Path | None
    interface: Path | None


def serve(
    registry: TableRegistry,
    gatherings: Gatherings,
    settings: Settings,
    choice: Choice,
    artwork: Artwork,
) -> Hosted:
    """Put one gathering into service: the room a company arrives at, and the table it comes to be dealt.

    Everything a player interface needs answers from the single application this builds — the games on offer
    and the gathering that settles among them, the endpoints of the table under `/tables` once it is dealt, the
    cards it draws with under `/artwork` where a pack has been fetched, and the page itself at the root where a
    build of it exists. The artwork goes on ahead of the page, since the page is mounted at the root and
    everything answering for itself is registered before it.

    The gathering is handed to the application twice over: the endpoints a table is played at ask it what seat
    a credential holds, and the endpoints a table is gathered at ask it for the room itself. That is what makes
    an arrival the whole of identity here, since the token minted at one is the token that goes on to play.

    Args:
        registry: the tables in service, which is where a dealt gathering lands.
        gatherings: the lobby, holding what is offered and how a settled choice becomes a table.
        settings: the name the table gathers under, the code it gathers behind, and how it runs.
        choice: what the gathering opens at, which its company settles from there.
        artwork: which cards the table is drawn with.

    Raises:
        GameValidationError: when the opening choice names a game offered nowhere, a table that game seats
            nowhere, or a count of decks it is dealt from nowhere.
    """
    gatherings.open(settings.name, settings.code, choice)
    app = create_app(registry, gatherings, gatherings)
    return Hosted(
        app=app,
        table=settings.name,
        code=settings.code,
        artwork=serve_artwork(app, ASSETS, artwork),
        interface=serve_interface(app, INTERFACE),
    )
