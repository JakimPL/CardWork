from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from http import HTTPStatus
from typing import Final

from httpx import ASGITransport, AsyncClient

from cardgames.frontend.climbing.layout import CLIMBING_SCENE
from cardgames.frontend.passing.layout import PASSING_SCENE
from cardgames.frontend.shedding.layout import SHEDDING_SCENE
from cardgames.frontend.showdown.layout import SHOWDOWN_SCENE
from cardserver.gathering import FIRST_REVISION, TINTS
from cardserver.identity import SEAT_HEADER
from cardserver.naming import Seated
from cardserver.schemas import (
    Admitted,
    Arriving,
    Choice,
    Claiming,
    Dealing,
    GatheringView,
    MoveRequest,
    Readying,
)
from cardtable.catalogue import opened
from cardtable.games import GameName
from cardtable.hosting import Hosted
from cardtable.settings import Settings
from cardwork.decks.standard import ONE_DECK
from cardwork.presentation.scene import Scene
from cardwork.rounds.conclusion import Conclusion
from tests.cases import Case

from .config import ADMIN, ADVANCED, CODE, GLYPHS

TABLE: Final[str] = "green-baize"
UNSERVED: Final[str] = "no-such-table"
PLAYERS: Final[int] = 3
ROUNDS: Final[int] = 2
SEED: Final[int] = 20260803
NO_GRACE: Final[float] = 0.0
BASE_URL: Final[str] = "http://cardwork"

NAMES: Final[tuple[str, ...]] = (
    "Ada",
    "Grace",
    "Alan",
    "Edsger",
    "Barbara",
    "Alonzo",
    "Emmy",
    "Donald",
)

SETTINGS: Final[Settings] = Settings(
    name=TABLE,
    code=CODE,
    seed=SEED,
    grace_seconds=NO_GRACE,
)

LAYOUT: Final[str] = f"/tables/{TABLE}/layout"
VIEW: Final[str] = f"/tables/{TABLE}/view"
MOVES: Final[str] = f"/tables/{TABLE}/moves"
GUESTS: Final[str] = f"/tables/{TABLE}/guests"
GATHERING: Final[str] = f"/tables/{TABLE}/gathering"
SEAT: Final[str] = f"/tables/{TABLE}/seat"
DEALING: Final[str] = f"/tables/{TABLE}/deal"
READY: Final[str] = f"/tables/{TABLE}/ready"


@dataclass(frozen=True)
class HostCase(Case):
    """One game the host holds, beside the scene its own module states for it.

    Naming the scene here rather than reading it back off the host is what makes the assertion say
    something: the layout a client is served has to be the one the game stated, not merely a layout.
    """

    game: GameName
    scene: Scene


CASES: Final[tuple[HostCase, ...]] = (
    HostCase(
        description="a game of four cards passed in turn",
        game=GameName.PASSING,
        scene=PASSING_SCENE,
    ),
    HostCase(
        description="a game of sealed cards turned over at once",
        game=GameName.SHOWDOWN,
        scene=SHOWDOWN_SCENE,
    ),
    HostCase(
        description="a game of sets shed from a hand that grows",
        game=GameName.SHEDDING,
        scene=SHEDDING_SCENE,
    ),
    HostCase(
        description="a game of combinations climbed over until one hand runs out",
        game=GameName.CLIMBING,
        scene=CLIMBING_SCENE,
    ),
)


def settled(game: GameName, players: int, decks: int) -> Choice:
    """The choice a gathering of that game stands at: a table of that size, dealt from that many decks."""
    return Choice(
        game=game.value,
        players=players,
        decks=decks,
        conclusion=Conclusion(rounds=ROUNDS),
    )


CHOICE: Final[Choice] = settled(GameName.PASSING, PLAYERS, ONE_DECK)


def a_company(players: int) -> Mapping[int, str]:
    """The name every seat of a table that size is taken under, in the order the seats are claimed."""
    return {seat: NAMES[seat] for seat in range(players)}


def a_seated_company(players: int) -> Mapping[int, Seated]:
    """The name and tint every seat is read by once such a company has arrived and sat in turn.

    The tints follow the arrivals rather than the seats, and these guests arrive in the order they sit, so the
    seat taken first plays under the first tint of the palette.
    """
    return {seat: Seated(name=NAMES[seat], tint=TINTS[seat]) for seat in range(players)}


@dataclass(frozen=True)
class Dealt:
    """One table dealt through its own gathering: the client reaching it, and the tokens its company holds.

    A seat is held by whoever arrived and claimed it, so the tokens here are the ones the gathering minted and
    the whole of what these tests speak for a seat through.
    """

    client: AsyncClient
    hosted: Hosted
    tokens: Mapping[int, str]

    def credentials(self, seat: int) -> dict[str, str]:
        """The header a client speaks for one seat of the table through."""
        return {SEAT_HEADER: self.tokens[seat]}


async def arrives(client: AsyncClient, code: str, name: str) -> Admitted:
    """One guest arriving at the table on a code, answered with the token they speak through.

    Raises:
        HTTPStatusError: when the gathering turned the arrival away.
    """
    arriving = Arriving(code=code, name=name)
    response = await client.post(GUESTS, json=arriving.model_dump(mode="json"))
    response.raise_for_status()
    return Admitted.model_validate(response.json())


async def sits(client: AsyncClient, token: str, seat: int, base_revision: int) -> GatheringView:
    """One guest taking a seat, answered with the gathering as they read it afterwards.

    Raises:
        HTTPStatusError: when the gathering refused the seat.
    """
    claiming = Claiming(seat=seat, base_revision=base_revision)
    response = await client.put(
        SEAT,
        json=claiming.model_dump(mode="json"),
        headers={SEAT_HEADER: token},
    )
    response.raise_for_status()
    return GatheringView.model_validate(response.json())


async def deals(client: AsyncClient, token: str, base_revision: int) -> GatheringView:
    """One guest calling for the deal, answered with the gathering it ended.

    Raises:
        HTTPStatusError: when the gathering refused the deal.
    """
    dealing = Dealing(base_revision=base_revision)
    response = await client.post(
        DEALING,
        json=dealing.model_dump(mode="json"),
        headers={SEAT_HEADER: token},
    )
    response.raise_for_status()
    return GatheringView.model_validate(response.json())


async def readies(client: AsyncClient, token: str, base_revision: int) -> GatheringView:
    """One seated guest committing to the settings, answered with the gathering as they read it afterwards.

    Raises:
        HTTPStatusError: when the gathering refused the commitment.
    """
    readying = Readying(ready=True, base_revision=base_revision)
    response = await client.put(
        READY,
        json=readying.model_dump(mode="json"),
        headers={SEAT_HEADER: token},
    )
    response.raise_for_status()
    return GatheringView.model_validate(response.json())


async def a_dealt_table(client: AsyncClient, code: str, players: int) -> Mapping[int, str]:
    """Gather a company that fills the table, seat and commit each of them in turn, and deal what they settled on.

    Every command quotes the revision the one before it was answered with, which is how a client acts on what
    it has just heard from a gathering.

    Raises:
        HTTPStatusError: when the gathering refused a step, which leaves the table undealt.
    """
    tokens: dict[int, str] = {}
    revision = FIRST_REVISION
    for seat, name in a_company(players).items():
        admitted = await arrives(client, code, name)
        tokens[seat] = admitted.token
        revision = (await sits(client, admitted.token, seat, admitted.gathering.revision)).revision

    for seat in sorted(tokens):
        revision = (await readies(client, tokens[seat], revision)).revision

    await deals(client, tokens[0], revision)
    return tokens


@asynccontextmanager
async def gathering(choice: Choice) -> AsyncIterator[tuple[AsyncClient, Hosted]]:
    """One table gathering at that choice through the host, with nobody arrived at it yet.

    The application's own lifespan runs around the client, so the table ends these tests holding no timer
    the way it ends its service under a server. The table draws with the glyphs its page carries, which
    leaves these reading the endpoints alone whether or not the checkout has fetched a pack.
    """
    hosted = opened(SETTINGS, choice, GLYPHS, ADVANCED, ADMIN)
    async with hosted.app.router.lifespan_context(hosted.app):
        async with AsyncClient(transport=ASGITransport(app=hosted.app), base_url=BASE_URL) as client:
            yield client, hosted


@asynccontextmanager
async def playing(game: GameName) -> AsyncIterator[Dealt]:
    """One table of that game gathered, seated and dealt through the host, as a client reaching it does.

    A table is dealt by the company that gathered at it, so the arrivals here are what mint the tokens these
    tests read through: a guest arrives on the code, takes a seat, and the table is dealt once every seat is
    taken.
    """
    async with gathering(settled(game, PLAYERS, ONE_DECK)) as (client, hosted):
        yield Dealt(
            client=client,
            hosted=hosted,
            tokens=await a_dealt_table(client, hosted.code, PLAYERS),
        )


async def a_seat_to_act(dealt: Dealt) -> tuple[int, dict[str, object], int]:
    """A seat the table holds a move for, one of the moves it may make, and the sequence it stands at.

    The moves come from the seat's own view, which is how an interface reads them, so a seat found here is
    one a client would have been offered something to do.

    Raises:
        ValueError: when no seat of the table is offered a move, which a table in play never reaches.
    """
    for seat in range(PLAYERS):
        served = (await dealt.client.get(VIEW, headers=dealt.credentials(seat))).json()
        if served["legal"]:
            return seat, served["legal"][0], served["seq"]

    raise ValueError(f"Table {dealt.hosted.table!r} offers no seat a move to make")


async def submit(
    dealt: Dealt,
    seat: int,
    move: dict[str, object],
    base_seq: int,
) -> HTTPStatus:
    """Send one move as the seat holding it, and answer with the status the table met it with."""
    command = MoveRequest.model_validate({"move": move, "base_seq": base_seq, "idempotency_key": "the-first-try"})
    response = await dealt.client.post(
        MOVES,
        json=command.model_dump(mode="json"),
        headers=dealt.credentials(seat),
    )
    return HTTPStatus(response.status_code)
