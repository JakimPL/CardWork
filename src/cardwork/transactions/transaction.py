from typing import Generic

from cardwork.effects.effects import Effects
from cardwork.models.base import BaseFrozen
from cardwork.moves.move import Move
from cardwork.states.state import GameState, StateT


class Transaction(BaseFrozen, Generic[StateT]):
    """One atomic commit: everything it changed, plus the move that prompted it when a seat did.

    Storing the effects rather than the resulting position is what keeps the journal replayable and
    randomness resolved exactly once.
    """

    seq: int
    move: Move | None
    effects: Effects[StateT]


type Transactions[S: GameState] = tuple[Transaction[S], ...]
