from cardwork.models.base import BaseFrozen
from cardwork.zones.audience import Audience


class Visibility(BaseFrozen):
    face_up: Audience = Audience.ALL
    face_down: Audience = Audience.NONE
    extra: frozenset[int] = frozenset()
