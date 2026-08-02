from collections.abc import Mapping

from cardwork.effects.effect import Effect
from cardwork.moves.actions import NonEmptyIndices


class MoveCards(Effect):
    source: str
    indices: NonEmptyIndices
    target: str
    at: int | None = None
    face_down: bool | None = None


class SetFace(Effect):
    zone: str
    indices: NonEmptyIndices
    face_down: bool


class Reorder(Effect):
    zone: str
    order: tuple[int, ...]


class SetState(Effect):
    changes: Mapping[str, object]
