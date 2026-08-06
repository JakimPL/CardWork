from typing import Final, Self, TypeVar

from cardwork.models.base import BaseFrozen
from cardwork.states.seats import Seats

type Points = tuple[int, ...]

NOTHING: Final[int] = 0


class GameState(BaseFrozen):
    """The rules cursor every game shares: which phase is running, who owes an action, and the score.

    A game declares its own subclass with typed fields for anything else it tracks — a bid, the trump
    suit, the seat that led the trick — and parameterises the engine with that subclass, so those
    fields keep full type checking and exact serialization.

    `to_act` holds the seats that owe an action, and takes the turn as a game states it: a single seat, or
    any run of seats, reaches the field as the set of seats it names.
    """

    phase: str
    to_act: Seats = frozenset()
    points: Points | None = None

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

    def at_rest(self, phase: str, **changes: object) -> Self:
        """A state of this same type standing in that phase with no seat owing an action.

        A phase that closes something leaves nobody to act — a round decided, a match over, a hand played
        out — so this states the two together and carries whatever else that close writes.

        Raises:
            ValidationError: when a change leaves the state outside the types the game declared, or names a
                field the state does not declare.
        """
        return self.with_changes(phase=phase, to_act=frozenset(), **changes)

    def project(self, observer: int | None) -> Self:  # pylint: disable=unused-argument
        """The cursor as one observer is entitled to read it, which is the whole of it here.

        The three fields every game shares are table knowledge: the phase, the seats that owe an action
        and the running score are as public as the cards face up on the table. A game whose own state
        holds something a seat keeps to itself — sealed bids gathered during a simultaneous round, a
        privately drawn objective — overrides this to blank those fields for every other observer, so
        that the cursor crossing the wire obeys the same entitlement the cards do.

        Args:
            observer: the seat receiving the projection, or None for a spectator.
        """
        return self


StateT = TypeVar("StateT", bound=GameState)
