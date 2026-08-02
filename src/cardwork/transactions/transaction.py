from cardwork.effects.effect import Effects
from cardwork.models.base import BaseFrozen
from cardwork.moves.move import Move


class Transaction(BaseFrozen):
    seq: int
    move: Move | None
    effects: Effects


Transactions = tuple[Transaction, ...]
