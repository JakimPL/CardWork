from __future__ import annotations

from cardwork.effects.fold import fold
from cardwork.models.base import BaseFrozen
from cardwork.positions.position import Position
from cardwork.transactions.transaction import Transaction, Transactions


class Journal(BaseFrozen):
    initial: Position
    transactions: Transactions = ()

    @property
    def head(self) -> int:
        return len(self.transactions)

    def append(self, transaction: Transaction) -> Journal:
        return self.model_copy(update={"transactions": self.transactions + (transaction,)})

    def truncate(self) -> Journal:
        return self.model_copy(update={"transactions": self.transactions[:-1]})

    def replay(self, upto: int | None = None) -> Position:
        return fold(
            (effect for transaction in self.transactions[:upto] for effect in transaction.effects),
            self.initial,
        )
