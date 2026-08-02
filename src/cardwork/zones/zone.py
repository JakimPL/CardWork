from collections.abc import Mapping

from cardwork.decks.deck import GameCards
from cardwork.models.base import BaseFrozen
from cardwork.zones.visibility import Visibility


class Zone(BaseFrozen):
    id: str
    owner: int | None = None
    visibility: Visibility
    cards: GameCards


Zones = Mapping[str, Zone]
