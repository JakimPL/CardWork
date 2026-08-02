from cardwork.positions.position import Position
from cardwork.transactions.transaction import Transaction
from cardwork.views.event import EventView
from cardwork.views.position import PositionView


def project_position(
    position: Position,
    observer: int | None,
    players: int,
) -> PositionView: ...


def project_transaction(
    transaction: Transaction,
    position: Position,
    observer: int | None,
    players: int,
) -> EventView: ...
