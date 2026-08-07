from collections.abc import Callable
from http import HTTPStatus
from typing import Final

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response

from cardserver.protocols.table import TableId
from cardserver.schemas.error import ErrorBody
from cardwork.exceptions import (
    ArrangementRefused,
    GameValidationError,
    IllegalMove,
    NotYourTurn,
    StalePosition,
)


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


class Unauthorized(CardserverError):
    """Raised when the overseeing routes are reached without the token this host was started under.

    The token is handed to whoever runs the server and to nobody else, so a request offering none or another
    is turned away before it is read for what it asks: overseeing is the one thing here no code admits anyone to.
    """

    def __init__(self) -> None:
        super().__init__("These routes answer only to the token this host prints as it starts")


class JournalSealed(CardserverError):
    """Raised when the full record of a table is asked for while the game it belongs to is still on."""

    def __init__(self, table: TableId) -> None:
        super().__init__(f"The record of table {table!r} opens once its game is over")
        self.table = table


class Unadmitted(CardserverError):
    """Raised when what someone offered at a gathering admits them to it nowhere."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class NameTaken(CardserverError):
    """Raised when a guest arrives under a name the company already reads."""

    def __init__(self, name: str) -> None:
        super().__init__(f"The name {name!r} is already read at this table")
        self.name = name


class SeatTaken(CardserverError):
    """Raised when a seat is claimed while another guest of the company holds it."""

    def __init__(self, seat: int, held_by: str) -> None:
        super().__init__(f"Seat {seat} is held by {held_by!r}")
        self.seat = seat
        self.held_by = held_by


class TintTaken(CardserverError):
    """Raised when a tint is taken while another guest of the company holds it."""

    def __init__(self, tint: str, held_by: str) -> None:
        super().__init__(f"The {tint} tint is held by {held_by!r}")
        self.tint = tint
        self.held_by = held_by


class NoSuchSeat(CardserverError):
    """Raised when a seat is claimed that the table the gathering settled on holds nowhere."""

    def __init__(self, seat: int, players: int) -> None:
        super().__init__(f"Seat {seat} stands outside the {players} seats this table was settled on")
        self.seat = seat
        self.players = players


class NoSay(CardserverError):
    """Raised when a guest settles what a table plays, or calls for its deal, holding a say over neither."""

    def __init__(self, guest: str) -> None:
        super().__init__(f"{guest!r} holds no say over what this table plays")
        self.guest = guest


class GatheringOver(CardserverError):
    """Raised when a gathering is asked to change after the table it settled has been dealt."""

    def __init__(self, table: TableId) -> None:
        super().__init__(f"Table {table!r} is dealt and its gathering is over")
        self.table = table


class SeatsEmpty(CardserverError):
    """Raised when the deal is called for while a seat of the table stands empty."""

    def __init__(self, empty: tuple[int, ...]) -> None:
        super().__init__(f"A table is dealt once every seat is taken, and these stand empty: {sorted(empty)}")
        self.empty = empty


class StaleGathering(CardserverError):
    """Raised when a command is built on a revision the gathering has moved past since."""

    def __init__(self, base_revision: int, revision: int) -> None:
        super().__init__(f"The command was built on revision {base_revision} while the gathering stands at {revision}")
        self.base_revision = base_revision
        self.revision = revision


class NotReady(CardserverError):
    """Raised when the deal is called for while a seated guest has yet to commit to the settings."""

    def __init__(self, waiting: tuple[str, ...]) -> None:
        super().__init__(f"A table is dealt once every seat has committed, and these have not: {sorted(waiting)}")
        self.waiting = waiting


class NotTheHost(CardserverError):
    """Raised when a guest governs a table, or breaks it up, holding the host's say over neither."""

    def __init__(self, guest: str) -> None:
        super().__init__(f"{guest!r} is not the host of this table")
        self.guest = guest


class NoCreation(CardserverError):
    """Raised when a guest gathers a table where this host lets only its overseer open one."""

    def __init__(self) -> None:
        super().__init__("This host opens tables from its own panel just now, so ask whoever runs it for one")


class TablesFull(CardserverError):
    """Raised when a table is gathered while this host already holds as many as it opens at once."""

    def __init__(self, most: int) -> None:
        super().__init__(f"This host gathers {most} tables at once, and that many already stand")
        self.most = most


class TableClosed(CardserverError):
    """Raised when a table that has been broken up is asked for anything further."""

    def __init__(self, table: TableId) -> None:
        super().__init__(f"Table {table!r} has been closed")
        self.table = table


REFUSALS: Final[tuple[tuple[type[Exception], HTTPStatus], ...]] = (
    (Unauthenticated, HTTPStatus.UNAUTHORIZED),
    (Unauthorized, HTTPStatus.UNAUTHORIZED),
    (UnknownTable, HTTPStatus.NOT_FOUND),
    (WrongSeat, HTTPStatus.FORBIDDEN),
    (JournalSealed, HTTPStatus.FORBIDDEN),
    (NotYourTurn, HTTPStatus.FORBIDDEN),
    (StalePosition, HTTPStatus.CONFLICT),
    (IllegalMove, HTTPStatus.UNPROCESSABLE_ENTITY),
    (ArrangementRefused, HTTPStatus.UNPROCESSABLE_ENTITY),
    (Unadmitted, HTTPStatus.FORBIDDEN),
    (NoSay, HTTPStatus.FORBIDDEN),
    (NameTaken, HTTPStatus.CONFLICT),
    (SeatTaken, HTTPStatus.CONFLICT),
    (TintTaken, HTTPStatus.CONFLICT),
    (GatheringOver, HTTPStatus.CONFLICT),
    (SeatsEmpty, HTTPStatus.CONFLICT),
    (NotReady, HTTPStatus.CONFLICT),
    (StaleGathering, HTTPStatus.CONFLICT),
    (NotTheHost, HTTPStatus.FORBIDDEN),
    (NoCreation, HTTPStatus.FORBIDDEN),
    (TablesFull, HTTPStatus.SERVICE_UNAVAILABLE),
    (TableClosed, HTTPStatus.GONE),
    (NoSuchSeat, HTTPStatus.UNPROCESSABLE_ENTITY),
    (GameValidationError, HTTPStatus.UNPROCESSABLE_ENTITY),
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
