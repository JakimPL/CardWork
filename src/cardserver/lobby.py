from typing import Annotated, Final

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse

from cardserver.gathering import Gatherings
from cardserver.identity import SEAT_HEADER
from cardserver.protocol import TableId
from cardserver.schemas import (
    Admitted,
    Arriving,
    Choosing,
    Claiming,
    Dealing,
    GatheringView,
    Offering,
    Tinting,
)
from cardserver.streams import (
    EVENT_STREAM,
    STREAM_HEADERS,
    STREAM_START,
    attendance,
    resume_point,
)

UNKNOWN_CALLER: Final[str] = "unknown"


def caller_of(request: Request) -> str:
    """The address a request came from, which is what a turnstile counts a wrong code against."""
    client = request.client
    return UNKNOWN_CALLER if client is None else client.host


def gathering_routes(gatherings: Gatherings) -> APIRouter:
    """The routes a table is gathered at, which an application serving a lobby carries beside the rest.

    Arriving is the one of them open to a stranger, and it is open on the code alone: everything after it reads
    the guest off the token minted there, so a name authorises nothing and the company is known by what it
    holds. The room itself is behind the code as well, since the code is among the things the company holds.

    Args:
        gatherings: the tables gathering here, which is also where a credential becomes a seat.
    """
    router = APIRouter()

    def guest_of(
        table_id: str,
        credential: Annotated[str | None, Header(alias=SEAT_HEADER)] = None,
    ) -> str:
        """The guest this request speaks for at the gathering it names."""
        return gatherings.guest(table_id, credential)

    @router.get("/offerings")
    async def read_offerings() -> tuple[Offering, ...]:
        """Every game this host offers, and the tables and deck counts each of them is played with.

        A page draws its whole choice from this, which is what leaves it holding the name of no game.
        """
        return gatherings.offerings

    @router.get("/tables")
    async def read_tables() -> tuple[TableId, ...]:
        """The tables gathering here, which is what a page offers somebody who reached the server bare.

        Read without a credential, as the offerings are: what admits a person is the code, so naming what is
        gathering costs a table nothing and saves the one who was handed no line from guessing.
        """
        return gatherings.gathering()

    @router.post("/tables/{table_id}/guests")
    async def arrive(
        table_id: str,
        arriving: Arriving,
        request: Request,
    ) -> Admitted:
        """Admit one person on the code they offered, answering with the token they will speak through."""
        return gatherings.arrive(table_id, arriving, caller_of(request))

    @router.get("/tables/{table_id}/gathering")
    async def read_gathering(
        table_id: str,
        guest: Annotated[str, Depends(guest_of)],
    ) -> GatheringView:
        """The gathering as this guest reads it: the company, what is settled, and where it stands."""
        return gatherings.at(table_id).view(guest)

    @router.get("/tables/{table_id}/gathering/events")
    async def read_attendance(
        table_id: str,
        guest: Annotated[str, Depends(guest_of)],
        since: Annotated[int, Query(ge=0)] = STREAM_START,
        last_event_id: Annotated[int | None, Header(alias="Last-Event-ID")] = None,
    ) -> StreamingResponse:
        """How the gathering stands, again at every revision it reaches, until the table is dealt."""
        gathering = gatherings.at(table_id)
        stream = attendance(gathering, guest, resume_point(last_event_id, since))
        return StreamingResponse(
            stream,
            media_type=EVENT_STREAM,
            headers=STREAM_HEADERS,
        )

    @router.put("/tables/{table_id}/seat")
    async def claim_seat(
        table_id: str,
        claiming: Claiming,
        guest: Annotated[str, Depends(guest_of)],
    ) -> GatheringView:
        """Take a seat at the table, or stand up from the one held by naming none."""
        return gatherings.claim(table_id, guest, claiming)

    @router.put("/tables/{table_id}/tint")
    async def take_tint(
        table_id: str,
        tinting: Tinting,
        guest: Annotated[str, Depends(guest_of)],
    ) -> GatheringView:
        """Take one of the company's tints, which every guest may do for their own."""
        return gatherings.tint(table_id, guest, tinting)

    @router.put("/tables/{table_id}/choice")
    async def settle_choice(
        table_id: str,
        choosing: Choosing,
        guest: Annotated[str, Depends(guest_of)],
    ) -> GatheringView:
        """Settle what the table plays, which every guest holding a say may do."""
        return gatherings.choose(table_id, guest, choosing)

    @router.post("/tables/{table_id}/deal")
    async def deal_table(
        table_id: str,
        dealing: Dealing,
        guest: Annotated[str, Depends(guest_of)],
    ) -> GatheringView:
        """Deal the table the company settled on, which opens it and ends the gathering."""
        return gatherings.deal(table_id, guest, dealing)

    return router
