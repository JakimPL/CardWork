import asyncio
from collections.abc import AsyncIterator
from json import dumps
from typing import Final

from cardserver.gathering.gathering import Gathering
from cardserver.schemas.gathering import GatheringView
from cardserver.sessions.commit import Commit
from cardserver.sessions.in_service import InService

STREAM_START: Final[int] = 0
COMMIT_EVENT: Final[str] = "commit"
GATHERING_EVENT: Final[str] = "gathering"
CLOSED_EVENT: Final[str] = "closed"
EVENT_STREAM: Final[str] = "text/event-stream"
STREAM_HEADERS: Final[dict[str, str]] = {
    "Cache-Control": "no-store",
    "X-Accel-Buffering": "no",
}


def resume_point(
    last_event_id: int | None,
    since: int,
) -> int:
    """Where a stream picks up: after the last event a client acknowledged, or the point it asked for.

    Server-sent events carry the id a client hands back on reconnect, so a dropped stream resumes from a
    header and catching up costs what staying connected costs.
    """
    return since if last_event_id is None else last_event_id + 1


def framed(
    identifier: int,
    event: str,
    body: str,
) -> str:
    """One event in the wire format of server-sent events, keyed by the id a client resumes from."""
    return f"id: {identifier}\nevent: {event}\ndata: {body}\n\n"


def frame(
    event: Commit,
) -> str:
    """One commit in the wire format of server-sent events, keyed by the sequence it landed at."""
    return framed(event.seq, COMMIT_EVENT, event.model_dump_json())


def dismissed(
    session: InService,
) -> str:
    """The word a broken-up table leaves, which a stream carries last so a seat learns the game is over."""
    return framed(session.head, CLOSED_EVENT, dumps({"reason": session.closing}))


def standing(
    view: GatheringView,
) -> str:
    """How a gathering stands, keyed by the revision it had reached when it was read."""
    return framed(view.revision, GATHERING_EVENT, view.model_dump_json())


def broken(
    view: GatheringView,
) -> str:
    """The word a broken-up gathering leaves, which a stream carries last so a page learns the room is gone."""
    return framed(view.revision, CLOSED_EVENT, dumps({"reason": view.reason}))


async def commits(
    session: InService,
    observer: int | None,
    since: int,
    patience: float,
) -> AsyncIterator[str]:
    """Every commit from `since` onward as one observer learns of it, waiting out the patience for the first.

    The journal is the stream's buffer, so a client is served from the record itself and the session only has
    to say when there is more. A slow reader falls behind and catches up; nothing is dropped and nothing is
    held for it.

    A stream carries what the table has to say and ends there, and the client picks it up again from the commit
    it acknowledged. Ending is what puts each answer whole on the wire, so a host that hands an answer on once
    it is finished carries a table as promptly as one that passes every write straight through.

    Taking the stream up is what reads the table as one somebody is at, which is what a reaper counts it alive
    by: a company thinking over a turn commits nothing for as long as the thinking takes, and a page following
    them says they are there throughout.

    A client asking from beyond where the record goes is served from the end of the record instead, so a page
    holding the sequence of a table that once stood under this name is carried back to the table that stands
    there now by the next commit landing on it.
    """
    session.attends()
    cursor = min(since, session.head)
    events = session.events(observer, cursor)
    if not events and not session.closed:
        try:
            await asyncio.wait_for(session.watch(cursor), patience)
        except TimeoutError:
            return

        events = session.events(observer, cursor)

    for event in events:
        yield frame(event)

    if session.closed:
        yield dismissed(session)


async def attendance(
    gathering: Gathering,
    guest: str,
    since: int,
    patience: float,
) -> AsyncIterator[str]:
    """How a gathering stands once it reaches `since`, waiting out the patience for it to get there.

    A gathering is a room rather than a record, so the frame carries the whole of how it stands and a client
    holds the last one it read. Opening the stream is what reads this guest as here, which is what makes the
    company a page draws the company watching it: the word stands for a while, so a page that keeps following
    keeps its place in the room and one that is gone falls out of it.

    A stream carries the room once and ends there, and the client picks it up again at the revision after the
    frame it read. A room that has moved several times over meets the next stream as it now stands, so catching
    up costs one frame however far behind it fell, and a room that stands still is asked for afresh.

    The deal is the last thing a gathering has to say, so the frame carrying it is the last one there is to
    read. Breaking the gathering up is the other last word: the stream carries a frame of its own for it, so a
    page learns the room is gone rather than watching it fall silent.
    """
    gathering.attends(guest)
    try:
        view = await asyncio.wait_for(gathering.since(since, guest), patience)
    except TimeoutError:
        return

    if view.closed:
        yield broken(view)
        return

    yield standing(view)
