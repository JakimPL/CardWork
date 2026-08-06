from collections.abc import AsyncIterator
from typing import Final

from cardserver.gathering import Gathering
from cardserver.schemas import GatheringView
from cardserver.sessions import Commit, InService

STREAM_START: Final[int] = 0
COMMIT_EVENT: Final[str] = "commit"
GATHERING_EVENT: Final[str] = "gathering"
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


def standing(
    view: GatheringView,
) -> str:
    """How a gathering stands, keyed by the revision it had reached when it was read."""
    return framed(view.revision, GATHERING_EVENT, view.model_dump_json())


async def commits(
    session: InService,
    observer: int | None,
    since: int,
) -> AsyncIterator[str]:
    """Every commit from `since` onward as one observer learns of it, and each further one as it lands.

    The journal is the stream's buffer, so a client is served from the record itself and the session
    only has to say when there is more. A slow reader falls behind and catches up; nothing is dropped
    and nothing is held for it.
    """
    cursor = since
    while True:
        events = session.events(observer, cursor)
        for event in events:
            yield frame(event)

        cursor += len(events)
        await session.watch(cursor)


async def attendance(
    gathering: Gathering,
    guest: str,
    since: int,
) -> AsyncIterator[str]:
    """How a gathering stands from `since` onward, again at every revision it reaches, until it is dealt.

    A gathering is a room rather than a record, so each frame carries the whole of how it stands and a client
    holds the last one it read. The guest is read as present for as long as the stream is held, which is what
    makes the company a page draws the company watching it, and hanging up takes their name out of the room.

    The deal is the last thing a gathering has to say, so the frame carrying it closes the stream and every page
    holding one is carried to the table by it.
    """
    gathering.attends(guest)
    try:
        cursor = since
        while True:
            view = await gathering.since(cursor, guest)
            yield standing(view)
            if view.dealt:
                return

            cursor = view.revision + 1
    finally:
        gathering.leaves(guest)
