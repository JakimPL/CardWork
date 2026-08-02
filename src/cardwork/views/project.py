from cardwork.positions.position import Position
from cardwork.states.state import StateT
from cardwork.transactions.transaction import Transaction
from cardwork.views.event import EventView
from cardwork.views.position import PositionView


def project_position(
    position: Position[StateT],
    observer: int | None,
) -> PositionView[StateT]: ...


def project_transaction(
    transaction: Transaction[StateT],
    before: Position[StateT],
    after: Position[StateT],
    observer: int | None,
) -> EventView: ...
