from collections.abc import Mapping
from typing import Generic

from cardwork.decks.deck import NonEmptyIndices
from cardwork.effects.effect import Effect
from cardwork.states.state import StateT
from cardwork.zones.zone import ZoneId


class MoveCards(Effect[StateT], Generic[StateT]):
    source: ZoneId
    indices: NonEmptyIndices
    target: ZoneId
    at: int | None = None
    face_down: bool | None = None


class SetFace(Effect[StateT], Generic[StateT]):
    zone: ZoneId
    indices: NonEmptyIndices
    face_down: bool


class Reorder(Effect[StateT], Generic[StateT]):
    zone: ZoneId
    order: tuple[int, ...]


class SetState(Effect[StateT], Generic[StateT]):
    changes: Mapping[str, object]
