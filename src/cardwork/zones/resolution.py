from cardwork.cards.game import GameCard
from cardwork.zones.audience import Audience
from cardwork.zones.zone import Zone


def audience(zone: Zone, card: GameCard, players: int) -> frozenset[int]:
    rule = zone.visibility.face_down if card.face_down else zone.visibility.face_up
    match rule:
        case Audience.ALL:
            base = frozenset(range(players))
        case Audience.OWNER:
            base = frozenset() if zone.owner is None else frozenset({zone.owner})
        case Audience.NONE:
            base = frozenset()
        case _:
            raise ValueError(f"Unexpected audience value: {rule}")

    return base | zone.visibility.extra
