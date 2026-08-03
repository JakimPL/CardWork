from __future__ import annotations

import asyncio
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Final, Self

from fastapi import FastAPI

Message = dict[str, Any]
PATIENCE: Final[float] = 5.0


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
        message = await self._written()
        return int(message["status"])

    async def frame(self) -> str:
        """The next chunk the application writes, which for an event stream is one whole frame."""
        message = await self._written()
        return str(message["body"].decode())

    async def _written(self) -> Message:
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
