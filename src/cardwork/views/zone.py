from cardwork.cards.game import GameCard
from cardwork.models.base import BaseFrozen
from cardwork.zones.zone import ZoneId


class ZoneView(BaseFrozen):
    """A zone as one observer sees it, with a placeholder standing in for every card outside their audience.

    Each placeholder keeps the index of the card it conceals, so an action addressing position 3 of a
    hand names the same card to the client and to the server.

    `arrangeable` is this observer's own answer to whether they may lay the zone out as they please, which the
    server resolves out of the zone's owner and arrangement for the same reason it narrows the cards: what a
    client may do arrives from the table rather than being worked out from what it was served.
    """

    id: ZoneId
    owner: int | None
    arrangeable: bool
    cards: tuple[GameCard | None, ...]
