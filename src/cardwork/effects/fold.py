from collections.abc import Iterable

from cardwork.effects.effect import Effect
from cardwork.positions.position import Position


def fold(effects: Iterable[Effect], position: Position) -> Position:
    for effect in effects:
        position = effect.apply(position)

    return position
