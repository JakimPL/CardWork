from abc import ABC, abstractmethod
from typing import Generic

from cardwork.models.base import BaseFrozen
from cardwork.positions.position import Position
from cardwork.states.state import GameState, StateT


class Effect(BaseFrozen, ABC, Generic[StateT]):
    """One primitive, replayable change to a position.

    Effects are the only writers of a position, which is what lets a transaction be stored as plain
    data and replayed to the same result.
    """

    @abstractmethod
    def apply(self, position: Position[StateT]) -> Position[StateT]:
        """The position resulting from this change, leaving the argument as it was."""


type Effects[S: GameState] = tuple[Effect[S], ...]
