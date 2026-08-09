from typing import Final

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

KEEPING: Final[str] = "cache-control"
UNKEPT: Final[str] = "no-store"
ASKED: Final[str] = "http"
ANSWERING: Final[str] = "http.response.start"


class Keeping:
    """States how long an answer may be kept, over every answer that says nothing of it itself.

    What this server answers is how a room stands at the moment it was asked, so an answer handed back out of
    a store is a room that has moved on: a page reading a kept view builds its commands on the revision that
    view carried and is told the gathering has left it behind. A host that finds an answer stating no policy
    settles one of its own — a month is a common one — which is what makes an answer state it here, since the
    one stated is the one every store between the table and the page goes by.

    An answer that states a policy keeps the one it states, so a built interface is still kept by the year,
    the page reaching it is still read afresh each time a tab opens, and a stream is still stored nowhere.
    """

    def __init__(self, app: ASGIApp, policy: str) -> None:
        self._app = app
        self._policy = policy

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Hand one request to the application, and state the policy over the answer as it goes out."""
        if scope["type"] != ASKED:
            await self._app(scope, receive, send)
            return

        async def stating(message: Message) -> None:
            if message["type"] == ANSWERING:
                MutableHeaders(scope=message).setdefault(KEEPING, self._policy)

            await send(message)

        await self._app(scope, receive, stating)
