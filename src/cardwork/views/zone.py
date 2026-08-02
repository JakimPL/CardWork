from cardwork.cards.game import GameCard
from cardwork.models.base import BaseFrozen


class ZoneView(BaseFrozen):
    id: str
    owner: int | None
    cards: tuple[GameCard | None, ...]
