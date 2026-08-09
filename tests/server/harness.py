from __future__ import annotations

import asyncio
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Final, Self

from fastapi import FastAPI

Message = dict[str, Any]
PATIENCE: Final[float] = 5.0
RESUME_HEADER: Final[str] = "Last-Event-ID"
ID_LINE: Final[str] = "id: "
ACROSS: Final[int] = 2


async def run_lifespan(app: FastAPI) -> list[str]:
    """Start an application and shut it down the way a server does, and report what it said.

    The in-process client speaks only of requests, so the one part of service a test reaches no other
    way is the pair of moments around them.
    """
    asked: list[Message] = [{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}]
    answered: list[Message] = []

    async def receive() -> Message:
        return asked.pop(0)

    async def send(message: Message) -> None:
        answered.append(message)

    await app(
        {"type": "lifespan", "asgi": {"version": "3.0"}, "state": {}},
        receive,
        send,
    )
    return [str(message["type"]) for message in answered]


class Streamed:
    """One request left open and read message by message, the way a real server reads a stream.

    An in-process HTTP client gathers a whole response before handing it over, which a stream that
    stays open never becomes. Driving the application directly is what lets a test read frames as they
    are written and hang up afterwards, and it runs the same routes, dependencies and response the
    client would have reached.
    """

    def __init__(
        self,
        app: FastAPI,
        path: str,
        headers: Mapping[str, str],
    ) -> None:
        self._app = app
        self._path = path
        self._headers = headers
        self._messages: asyncio.Queue[Message] = asyncio.Queue()
        self._hangup = asyncio.Event()
        self._asked = False
        self._request: asyncio.Task[None] | None = None

    async def __aenter__(self) -> Self:
        self._request = asyncio.create_task(
            self._app(
                self._scope(),
                self._receive,
                self._send,
            )
        )
        return self

    async def __aexit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._hangup.set()
        if self._request is not None:
            self._request.cancel()
            await asyncio.wait((self._request,))

    async def status(self) -> int:
        """The status the application answered with, read from the head of the response."""
        message = await self.written()
        return int(message["status"])

    async def frame(self) -> str:
        """The next chunk the application writes, which for an event stream is one whole frame."""
        message = await self.written()
        return str(message["body"].decode())

    async def written(self) -> Message:
        """The next message the application sends, which a stream that stalls gives up waiting for.

        Raises:
            TimeoutError: when nothing is written inside the patience a test has for it, which turns a
                stream that never wakes into a failure rather than a run that never ends.
        """
        return await asyncio.wait_for(self._messages.get(), timeout=PATIENCE)

    def _scope(self) -> Message:
        path, _, query = self._path.partition("?")
        return {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "path": path,
            "raw_path": path.encode(),
            "query_string": query.encode(),
            "headers": [(key.lower().encode(), value.encode()) for key, value in self._headers.items()],
            "scheme": "http",
            "server": ("cardwork", 80),
            "client": ("127.0.0.1", 123),
            "root_path": "",
        }

    async def _receive(self) -> Message:
        if not self._asked:
            self._asked = True
            return {"type": "http.request", "body": b"", "more_body": False}

        await self._hangup.wait()
        return {"type": "http.disconnect"}

    async def _send(self, message: Message) -> None:
        await self._messages.put(message)


def an_event_id(frame: str) -> int | None:
    """The id one frame is keyed by, which is where a client picks the stream up after reading it."""
    for line in frame.splitlines():
        if line.startswith(ID_LINE):
            return int(line.removeprefix(ID_LINE))

    return None


class Following:
    """A stream read the way a page reads it: one request after another, each picked up where the last left off.

    A stream stands for a spell and ends, so following one is a run of requests rather than a single answer.
    Each request states the frame the last one ended on, and the server begins after it, which is what makes
    the frames read through here the frames a client would have read whichever request carried them.
    """

    def __init__(
        self,
        app: FastAPI,
        path: str,
        headers: Mapping[str, str],
    ) -> None:
        self._app = app
        self._path = path
        self._headers = dict(headers)
        self._stream: Streamed | None = None
        self._status = 0
        self._read: int | None = None
        self._spent = True

    async def __aenter__(self) -> Self:
        await self._open()
        return self

    async def __aexit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._close()

    async def status(self) -> int:
        """The status the stream standing now was answered with."""
        return self._status

    async def frame(self) -> str:
        """The next frame this client reads, from the stream standing now or from the one picked up after it.

        Raises:
            TimeoutError: when two streams running out carry nothing at all, which is a room that never woke.
        """
        for _ in range(ACROSS):
            carried = await self._carried()
            if carried is not None:
                return carried

            await self._again()

        raise TimeoutError("no frame arrived across two streams, where a client following would have read one")

    async def quiet(self) -> bool:
        """Whether a stream picked up from here carries nothing at all before its patience runs out."""
        await self._again()
        return await self._carried() is None

    async def _carried(self) -> str | None:
        """The next frame the stream standing now writes, and None once it has ended."""
        if self._spent:
            return None

        message = await self._current().written()
        if not message.get("more_body", False):
            self._spent = True
            return None

        carried = str(message["body"].decode())
        keyed = an_event_id(carried)
        if keyed is not None:
            self._read = keyed

        return carried

    def _current(self) -> Streamed:
        """The stream standing now.

        Raises:
            RuntimeError: when a following is read before it has been opened.
        """
        if self._stream is None:
            raise RuntimeError("a following carries frames once it has been opened")

        return self._stream

    async def _open(self) -> None:
        """Ask for the stream afresh, stating the frame the last one ended on."""
        headers = dict(self._headers)
        if self._read is not None:
            headers[RESUME_HEADER] = str(self._read)

        self._stream = Streamed(self._app, self._path, headers)
        await self._stream.__aenter__()
        self._status = await self._stream.status()
        self._spent = False

    async def _close(self) -> None:
        """Hang up on the stream standing now, the way a page that stops following does."""
        if self._stream is not None:
            await self._stream.__aexit__(None, None, None)
            self._stream = None

    async def _again(self) -> None:
        """Hang up and ask again, which is the whole of how a client keeps following."""
        await self._close()
        await self._open()
