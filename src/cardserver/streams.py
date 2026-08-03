from collections.abc import AsyncIterator
from typing import Final

from cardserver.sessions import TableSession
from cardwork.states.state import StateT
from cardwork.views.event import EventView

STREAM_START: Final[int] = 0
COMMIT_EVENT: Final[str] = "commit"


def resume_point(
    last_event_id: int | None,
    since: int,
) -> int:
    """Where a stream picks up: after the last commit a client acknowledged, or the point it asked for.

    Server-sent events carry the sequence number as their id and hand it back on reconnect, so a
    dropped stream resumes from a header and catching up costs what staying connected costs.
    """
    return since if last_event_id is None else last_event_id + 1


def frame(
    event: EventView[StateT],
) -> str:
    """One commit in the wire format of server-sent events, keyed by the sequence it landed at."""
    return f"id: {event.seq}\nevent: {COMMIT_EVENT}\ndata: {event.model_dump_json()}\n\n"


async def commits(
    session: TableSession[StateT],
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
