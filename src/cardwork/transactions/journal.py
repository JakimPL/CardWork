from typing import Generic

from cardwork.effects.fold import fold
from cardwork.models.base import BaseFrozen
from cardwork.positions.position import Position
from cardwork.states.state import StateT
from cardwork.transactions.transaction import Transaction, Transactions


class Journal(BaseFrozen, Generic[StateT]):
    """The origin position plus every transaction committed since, in commit order.

    The journal is the table's record of truth: any position it has ever held is `replay(seq)`.
    """

    initial: Position[StateT]
    transactions: Transactions[StateT] = ()

    @property
    def head(self) -> int:
        return len(self.transactions)

    def append(self, transaction: Transaction[StateT]) -> "Journal[StateT]":
        return self.model_copy(update={"transactions": self.transactions + (transaction,)})

    def truncate(self) -> "Journal[StateT]":
        return self.model_copy(update={"transactions": self.transactions[:-1]})

    def replay(self, upto: int | None = None) -> Position[StateT]:
        """The position after the first `upto` transactions, or after all of them when `upto` is None."""
        return fold(
            (effect for transaction in self.transactions[:upto] for effect in transaction.effects),
            self.initial,
        )
