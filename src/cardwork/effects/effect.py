from abc import ABC, abstractmethod

from cardwork.models.base import BaseFrozen
from cardwork.positions.position import Position


class Effect(BaseFrozen, ABC):
    @abstractmethod
    def apply(self, position: Position) -> Position: ...


Effects = tuple[Effect, ...]
