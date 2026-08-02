from cardwork.cards.game import GameCard
from cardwork.models.base import BaseFrozen
from cardwork.zones.zone import ZoneId


class ZoneView(BaseFrozen):
    """A zone as one observer sees it, with a placeholder standing in for every card outside their audience.

    Each placeholder keeps the index of the card it conceals, so an action addressing position 3 of a
    hand names the same card to the client and to the server.
    """

    id: ZoneId
    owner: int | None
    cards: tuple[GameCard | None, ...]
