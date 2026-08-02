from typing import Self, TypeVar

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

    def with_changes(self, **changes: object) -> Self:
        """A state of this same type carrying the given changes, validated as though freshly built.

        This is how a game derives the next cursor: `model_copy` writes whatever it is handed, whereas
        every field this touches is checked against the game's own declared types before the result can
        reach a `SetState` and the journal.

        Raises:
            ValidationError: when a change leaves the state outside those types, or names a field the
                state does not declare.
        """
        return type(self).model_validate({**dict(self), **changes})


StateT = TypeVar("StateT", bound=GameState)
