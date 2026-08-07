from dataclasses import dataclass
from pathlib import Path
from secrets import token_urlsafe
from time import monotonic
from typing import Final

from fastapi import FastAPI

from cardserver.advanced import Advanced
from cardserver.app import create_app
from cardserver.gathering.gatherings import Gatherings
from cardserver.oversight.lobby.setting import NO_LIMIT
from cardserver.oversight.oversight import Oversight
from cardserver.oversight.token_admin import TokenAdmin
from cardserver.protocols.table import TableId
from cardserver.registry import TableRegistry
from cardserver.schemas.choice import Choice
from cardtable.admin import Admin
from cardtable.artwork import Artwork, serve_artwork
from cardtable.interface import serve_interface
from cardtable.paths import ASSETS, INTERFACE
from cardtable.settings import Settings

ADMIN_TOKEN_BYTES: Final[int] = 32


@dataclass(frozen=True)
class Hosted:
    """One table gathering: the application answering for it, and what a person needs to reach it.

    The code is the whole of what a guest is handed, since a person names themselves on arrival and is minted the
    token they play through there. The admin token stands apart from it, since the panel answers to whoever runs
    the host rather than to anyone the host admits, and is read out where the host alone reads it. The state type
    of the game is settled as the table is dealt and stays inside, which is what lets one host put games whose
    cursors are of different shapes into service.
    """

    app: FastAPI
    table: TableId
    code: str
    admin_token: str
    artwork: Path | None
    interface: Path | None


def an_admin_token(secret: str | None) -> str:
    """The token the panel answers behind: the one a file pins, or a fresh hand of random bytes for this run.

    A run pinning no secret is minted a token nobody has held before, so a restart that names none oversees under
    a token of its own and the panel a run leaves behind it is reachable by whoever started that run alone.
    """
    return secret if secret is not None else token_urlsafe(ADMIN_TOKEN_BYTES)


def an_oversight(
    gatherings: Gatherings,
    registry: TableRegistry,
    token: str,
    advanced: Advanced,
) -> Oversight:
    """The overseer's view of this host's lobby, held under the terms the run is tuned to and the token it minted.

    The clock is the machine's own monotonic reading, the same one the gatherings count their idleness on, so a
    reap here and the ages a card reads are told against one clock.
    """
    return Oversight(
        gatherings,
        registry,
        TokenAdmin(token),
        monotonic,
        democratic=advanced.democratic,
        creation=advanced.creation,
        stale_seconds=advanced.stale_seconds,
        idle_seconds=advanced.idle_seconds,
        capacity=NO_LIMIT if advanced.capacity is None else advanced.capacity,
    )


def serve(
    registry: TableRegistry,
    gatherings: Gatherings,
    settings: Settings,
    choice: Choice,
    artwork: Artwork,
    *,
    advanced: Advanced,
    admin: Admin,
) -> Hosted:
    """Put one gathering into service: the room a company arrives at, the table it comes to be dealt, and the
    panel the overseer runs the whole lobby from.

    Everything a player interface needs answers from the single application this builds — the games on offer
    and the gathering that settles among them, the endpoints of the table under `/tables` once it is dealt, the
    cards it draws with under `/artwork` where a pack has been fetched, and the page itself at the root where a
    build of it exists. The artwork goes on ahead of the page, since the page is mounted at the root and
    everything answering for itself is registered before it.

    The gathering is handed to the application twice over: the endpoints a table is played at ask it what seat
    a credential holds, and the endpoints a table is gathered at ask it for the room itself. That is what makes
    an arrival the whole of identity here, since the token minted at one is the token that goes on to play.

    The oversight is handed alongside them, which is what opens the panel under `/admin` and lets a company
    gather its own tables: it holds the terms the lobby is governed by, clears the tables nobody is at on the
    sweep the run is tuned to, and answers only to the admin token this host mints or is pinned to.

    Args:
        registry: the tables in service, which is where a dealt gathering lands.
        gatherings: the lobby, holding what is offered and how a settled choice becomes a table.
        settings: the name the table gathers under, the code it gathers behind, and how it runs.
        choice: what the gathering opens at, which its company settles from there.
        artwork: which cards the table is drawn with.
        advanced: how a code is guarded, how the lobby is governed and capped, and how often it is cleared.
        admin: the secret the panel answers behind, or none to mint a token fresh for this run.

    Raises:
        GameValidationError: when the opening choice names a game offered nowhere, a table that game seats
            nowhere, or a count of decks it is dealt from nowhere.
    """
    token = an_admin_token(admin.secret)
    oversight = an_oversight(gatherings, registry, token, advanced)
    gatherings.open(
        settings.name,
        settings.code,
        choice,
        democratic=advanced.democratic,
    )
    app = create_app(
        registry,
        gatherings,
        gatherings,
        oversight,
        sweep_seconds=advanced.sweep_seconds,
    )
    return Hosted(
        app=app,
        table=settings.name,
        code=settings.code,
        admin_token=token,
        artwork=serve_artwork(app, ASSETS, artwork),
        interface=serve_interface(app, INTERFACE),
    )
