from __future__ import annotations

from typing import Generic

from cardwork.effects.fold import fold
from cardwork.exceptions import UndoUnavailable
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

    def append(self, transaction: Transaction[StateT]) -> Journal[StateT]:
        """The journal with one further commit closing it, numbered where the record continues.

        Checking the number here is what lets a sequence number double as an index: `replay(n)` folds
        the first `n` transactions, and the client quoting `base_seq` names the position it built on.

        Raises:
            ValueError: when the transaction carries a number other than the current head.
        """
        if transaction.seq != self.head:
            raise ValueError(f"Transaction {transaction.seq} was offered to a journal standing at {self.head}")

        return self.model_copy(update={"transactions": self.transactions + (transaction,)})

    def truncate(self) -> Journal[StateT]:
        """The journal with its most recent commit dropped, back to the position that preceded it.

        Raises:
            UndoUnavailable: when the journal stands at its origin, where the only record is the deal
                the table was built with.
        """
        if not self.transactions:
            raise UndoUnavailable("The journal stands at its origin, which leaves a commit still to make")

        return self.model_copy(update={"transactions": self.transactions[:-1]})

    def replay(self, upto: int | None = None) -> Position[StateT]:
        """The position after the first `upto` transactions, or after all of them when `upto` is None."""
        return fold(
            (effect for transaction in self.transactions[:upto] for effect in transaction.effects),
            self.initial,
        )
