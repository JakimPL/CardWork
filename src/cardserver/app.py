from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Final

from fastapi import Depends, FastAPI, Header, Query
from fastapi.responses import StreamingResponse

from cardserver.errors import install_error_handlers
from cardserver.identity import SEAT_HEADER, SeatPolicy, confirm_actor
from cardserver.registry import TableRegistry
from cardserver.schemas import MoveAccepted, MoveRequest
from cardserver.streams import STREAM_START, commits, resume_point
from cardwork.states.state import StateT
from cardwork.transactions.journal import Journal
from cardwork.views.position import PositionView

EVENT_STREAM: Final[str] = "text/event-stream"
STREAM_HEADERS: Final[dict[str, str]] = {"Cache-Control": "no-store", "X-Accel-Buffering": "no"}


def create_app(registry: TableRegistry[StateT], seats: SeatPolicy) -> FastAPI:
    """An application serving the tables of one registry to the clients one seat policy admits.

    The four endpoints are the whole of the protocol: a command goes up over `POST`, and everything
    coming down is a projection — the view a client joins on, the stream it follows, and the record it
    reads once the game is over. Both directions pass through the seat the credential holds, so what a
    client may do and what it may know come from the same answer.

    Args:
        registry: the tables in service, which the host opens before or during service.
        seats: how a credential becomes a seat at a table.
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
    ) -> MoveAccepted:
        """Commit a seat's move to a table, answering with the sequence it landed at."""
        confirm_actor(observer, command.move.player)
        session = registry.session(table_id)
        seq = await session.submit(command.move, command.base_seq, command.idempotency_key)
        return MoveAccepted(seq=seq)

    # The response type is generic in the game's state, which leaves FastAPI no schema to build from it.
    @app.get("/tables/{table_id}/view", response_model=None)
    async def read_view(
        table_id: str,
        observer: Annotated[int | None, Depends(observer_of)],
    ) -> PositionView[StateT]:
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
        return StreamingResponse(stream, media_type=EVENT_STREAM, headers=STREAM_HEADERS)

    # The response type is generic in the game's state, which leaves FastAPI no schema to build from it.
    @app.get("/tables/{table_id}/journal", response_model=None)
    async def read_journal(table_id: str) -> Journal[StateT]:
        """The table's full record, which opens to everyone once the host has called the game over.

        The record reads the same to every client, so the seat behind the request settles nothing here.
        """
        return registry.session(table_id).record

    return app
