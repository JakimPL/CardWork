from typing import TypeVar

from cardwork.models.base import BaseFrozen


class GameState(BaseFrozen):
    """The rules cursor every game shares: which phase is running, who owes an action, and the score.

    A game declares its own subclass with typed fields for anything else it tracks — a bid, the trump
    suit, the seat that led the trick — and parameterises the engine with that subclass, so those
    fields keep full type checking and exact serialization.
    """

    phase: str
    to_act: frozenset[int] = frozenset()
    points: tuple[int, ...] | None = None

    @property
    def current(self) -> int | None:
        """The single player to act while the phase is sequential, or None while several seats owe an action."""
        return next(iter(self.to_act)) if len(self.to_act) == 1 else None


StateT = TypeVar("StateT", bound=GameState)
