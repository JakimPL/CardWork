from collections.abc import Mapping

from cardwork.games.state import GameState
from cardwork.models.base import BaseFrozen
from cardwork.views.zone import ZoneView


class PositionView(BaseFrozen):
    observer: int | None
    seq: int
    zones: Mapping[str, ZoneView]
    state: GameState
