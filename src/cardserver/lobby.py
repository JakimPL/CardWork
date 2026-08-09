from typing import Annotated, Final

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse

from cardserver.gathering.gatherings import Gatherings
from cardserver.identity.headers import SEAT_HEADER
from cardserver.oversight.oversight import Oversight
from cardserver.protocols.table import TableId
from cardserver.schemas.admitted import Admitted
from cardserver.schemas.arriving import Arriving
from cardserver.schemas.choosing import Choosing
from cardserver.schemas.claiming import Claiming
from cardserver.schemas.closing import Closing
from cardserver.schemas.dealing import Dealing
from cardserver.schemas.founding import Founding
from cardserver.schemas.gathering import GatheringView
from cardserver.schemas.governing import Governing
from cardserver.schemas.offering import Offering
from cardserver.schemas.readying import Readying
from cardserver.schemas.tinting import Tinting
from cardserver.streams import (
    EVENT_STREAM,
    STREAM_HEADERS,
    STREAM_START,
    attendance,
    resume_point,
)

UNKNOWN_CALLER: Final[str] = "unknown"


def caller_of(request: Request) -> str:
    """The address a request came from, which is what a turnstile counts a wrong code against.

    The client is the one the server resolves: a run trusting a reverse proxy's forwarding headers reads here
    the guest on the far side of it, and a run trusting none reads the peer it was spoken to directly.
    """
    client = request.client
    return UNKNOWN_CALLER if client is None else client.host


def gathering_routes(
    gatherings: Gatherings,
    oversight: Oversight | None = None,
    *,
    stream_patience: float,
) -> APIRouter:
    """The routes a table is gathered at, which an application serving a lobby carries beside the rest.

    Arriving is the one of them open to a stranger, and it is open on the code alone: everything after it reads
    the guest off the token minted there, so a name authorises nothing and the company is known by what it
    holds. The room itself is behind the code as well, since the code is among the things the company holds.

    Founding a table is the other route open to a stranger, and it stands where a run lets a company gather its
    own tables: the overseer holds how many may and who may, so this asks it before a table is opened and hands
    the founder the token that seats them at it.

    Args:
        gatherings: the tables gathering here, which is also where a credential becomes a seat.
        oversight: how many tables may stand and who may open one, and None where no company gathers its own.
        stream_patience: how long a stream on a gathering waits for the room to move before it ends.
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

    if oversight is not None:

        @router.post("/tables")
        async def found(founding: Founding) -> Admitted:
            """Gather a fresh table and seat its founder as the host, answering with the token they speak through."""
            return oversight.found(founding)

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
        """How the gathering stands, which a client reads again by asking again from where this leaves off."""
        gathering = gatherings.at(table_id)
        stream = attendance(gathering, guest, resume_point(last_event_id, since), stream_patience)
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

    @router.put("/tables/{table_id}/ready")
    async def commit_ready(
        table_id: str,
        readying: Readying,
        guest: Annotated[str, Depends(guest_of)],
    ) -> GatheringView:
        """Commit to the settings as they stand, or take that commitment back, which every seated guest may do."""
        return gatherings.ready(table_id, guest, readying)

    @router.put("/tables/{table_id}/governance")
    async def govern_table(
        table_id: str,
        governing: Governing,
        guest: Annotated[str, Depends(guest_of)],
    ) -> GatheringView:
        """Settle how the table is governed, which its host alone may do."""
        return gatherings.govern(table_id, guest, governing)

    @router.post("/tables/{table_id}/closing")
    async def close_gathering(
        table_id: str,
        closing: Closing,
        guest: Annotated[str, Depends(guest_of)],
    ) -> GatheringView:
        """Break the gathering up, which its host may call for, leaving the company a word on why."""
        gatherings.close(table_id, guest, closing)
        return gatherings.at(table_id).view(guest)

    return router
