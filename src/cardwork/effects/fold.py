from collections.abc import Iterable

from cardwork.effects.effect import Effect
from cardwork.positions.position import Position
from cardwork.states.state import StateT


def fold(
    effects: Iterable[Effect[StateT]],
    position: Position[StateT],
) -> Position[StateT]:
    """Apply effects in order, threading each result into the next."""
    for effect in effects:
        position = effect.apply(position)

    return position
