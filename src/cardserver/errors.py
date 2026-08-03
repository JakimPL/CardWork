from collections.abc import Callable
from http import HTTPStatus
from typing import Final

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response

from cardserver.protocol import TableId
from cardserver.schemas import ErrorBody
from cardwork.exceptions import IllegalMove, NotYourTurn, StalePosition


class CardserverError(Exception):
    """Root of the refusals the adapter answers on its own, before the rules have been asked anything."""


class UnknownTable(CardserverError):
    """Raised when a request names a table this server holds no session for."""

    def __init__(self, table: TableId) -> None:
        super().__init__(f"This server holds no table named {table!r}")
        self.table = table


class Unauthenticated(CardserverError):
    """Raised when a credential holds no seat at the table it was offered for."""

    def __init__(self, table: TableId) -> None:
        super().__init__(f"The credential offered holds no seat at table {table!r}")
        self.table = table


class WrongSeat(CardserverError):
    """Raised when the credential behind a command holds a seat other than the one the move was made for."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class JournalSealed(CardserverError):
    """Raised when the full record of a table is asked for while the game it belongs to is still on."""

    def __init__(self, table: TableId) -> None:
        super().__init__(f"The record of table {table!r} opens once its game is over")
        self.table = table


REFUSALS: Final[tuple[tuple[type[Exception], HTTPStatus], ...]] = (
    (Unauthenticated, HTTPStatus.UNAUTHORIZED),
    (UnknownTable, HTTPStatus.NOT_FOUND),
    (WrongSeat, HTTPStatus.FORBIDDEN),
    (JournalSealed, HTTPStatus.FORBIDDEN),
    (NotYourTurn, HTTPStatus.FORBIDDEN),
    (StalePosition, HTTPStatus.CONFLICT),
    (IllegalMove, HTTPStatus.UNPROCESSABLE_ENTITY),
)


def install_error_handlers(app: FastAPI) -> None:
    """Teach an application to answer every refusal the domain and the adapter state with its own status.

    Registering one handler per kind is what keeps the mapping total over the refusals listed and open
    at the edges: a game that raises its own subclass of one of them is answered the same way, and an
    error outside the list reaches the server as the defect it is.
    """
    for kind, status in REFUSALS:
        app.add_exception_handler(kind, _answer_with(status))


def _answer_with(status: HTTPStatus) -> Callable[[Request, Exception], Response]:
    """A handler naming the refusal and the sentence behind it, under the status that kind is owed."""

    def handle(_request: Request, error: Exception) -> Response:
        body = ErrorBody(error=type(error).__name__, detail=str(error))
        return JSONResponse(status_code=status, content=body.model_dump())

    return handle
