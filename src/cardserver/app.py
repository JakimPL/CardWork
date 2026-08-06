from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, Query
from fastapi.responses import StreamingResponse

from cardserver.errors import install_error_handlers
from cardserver.gathering import Gatherings
from cardserver.identity import SEAT_HEADER, SeatPolicy, confirm_actor, seated
from cardserver.lobby import gathering_routes
from cardserver.registry import TableRegistry
from cardserver.schemas import ArrangementRequest, CommandAccepted, MoveRequest
from cardserver.streams import (
    EVENT_STREAM,
    STREAM_HEADERS,
    STREAM_START,
    commits,
    resume_point,
)
from cardwork.models.base import BaseFrozen
from cardwork.presentation.layout import Layout


def create_app(
    registry: TableRegistry,
    seats: SeatPolicy,
    gatherings: Gatherings | None,
) -> FastAPI:
    """An application serving the tables of one registry to the clients one seat policy admits.

    The six endpoints of a table are the whole of the protocol it is played through: a command goes up over
    `POST`, which is the move a seat plays or the order it lays its own cards in, and everything coming down is
    read for one observer — the layout a client draws the table in, the view it joins on, the stream it follows,
    and the record it reads once the game is over. Both directions pass through the seat the credential holds,
    so what a client may do and what it may know come from the same answer.

    A table is gathered before it is dealt, and the routes that happens over are carried here as well, since a
    person reaches the room and the table at the one address. They ask for the whole lobby where the playing
    routes ask only for a seat, which is why the two arrive as two arguments: a host gathering its tables hands
    the same object over twice, and one serving a table already seated hands over a policy and no lobby at all.

    Args:
        registry: the tables in service, which the host opens before or during service.
        seats: how a credential becomes a seat at a table.
        gatherings: the tables gathering here, and None where this deployment gathers nobody.
    """

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await registry.close()

    app = FastAPI(title="CardWork", lifespan=lifespan)
    install_error_handlers(app)

    def observer_of(
        table_id: str,
        credential: Annotated[str | None, Header(alias=SEAT_HEADER)] = None,
    ) -> int | None:
        """The seat this request speaks for, and None for a spectator."""
        return seats.seat(table_id, credential)

    @app.post("/tables/{table_id}/moves")
    async def submit_move(
        table_id: str,
        command: MoveRequest,
        observer: Annotated[int | None, Depends(observer_of)],
    ) -> CommandAccepted:
        """Commit a seat's move to a table, answering with the sequence it landed at."""
        confirm_actor(observer, command.move.player)
        session = registry.session(table_id)
        seq = await session.submit(
            command.move,
            command.base_seq,
            command.idempotency_key,
        )
        return CommandAccepted(seq=seq)

    @app.post("/tables/{table_id}/arrangements")
    async def arrange_zone(
        table_id: str,
        command: ArrangementRequest,
        observer: Annotated[int | None, Depends(observer_of)],
    ) -> CommandAccepted:
        """Lay a zone of this seat's own out in the order it asks for, answering with the sequence it landed at.

        The seat comes off the credential rather than out of the request, so a client sorts the zones its own
        token holds and names no seat at all.
        """
        seat = seated(observer)
        session = registry.session(table_id)
        seq = await session.arrange(
            command.zone,
            command.order,
            seat,
            command.base_seq,
            command.idempotency_key,
        )
        return CommandAccepted(seq=seq)

    @app.get("/tables/{table_id}/layout")
    async def read_layout(
        table_id: str,
        observer: Annotated[int | None, Depends(observer_of)],
    ) -> Layout:
        """How this client lays the table out: the zones its seat holds and the moves it makes, and the
        shared table besides.

        A layout answers for the match rather than for the position, so a client asks once as it joins.
        """
        return registry.session(table_id).layout(observer)

    # The answer carries the cursor a game declares, which is one shape per game and so no schema at all.
    @app.get("/tables/{table_id}/view", response_model=None)
    async def read_view(
        table_id: str,
        observer: Annotated[int | None, Depends(observer_of)],
    ) -> BaseFrozen:
        """The table as this client is entitled to see it, stamped with the sequence it stands at."""
        return registry.session(table_id).view(observer)

    @app.get("/tables/{table_id}/events")
    async def read_events(
        table_id: str,
        observer: Annotated[int | None, Depends(observer_of)],
        since: Annotated[int, Query(ge=0)] = STREAM_START,
        last_event_id: Annotated[int | None, Header(alias="Last-Event-ID")] = None,
    ) -> StreamingResponse:
        """Every commit this client is entitled to, from where it left off and onward as they land."""
        session = registry.session(table_id)
        stream = commits(session, observer, resume_point(last_event_id, since))
        return StreamingResponse(
            stream,
            media_type=EVENT_STREAM,
            headers=STREAM_HEADERS,
        )

    # The answer carries the cursor a game declares, which is one shape per game and so no schema at all.
    @app.get("/tables/{table_id}/journal", response_model=None)
    async def read_journal(table_id: str) -> BaseFrozen:
        """The table's full record, which opens to everyone once the host has called the game over.

        The record reads the same to every client, so the seat behind the request settles nothing here.
        """
        return registry.session(table_id).record

    if gatherings is not None:
        app.include_router(gathering_routes(gatherings))

    return app
