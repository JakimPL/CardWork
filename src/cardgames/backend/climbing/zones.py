from cardwork.zones.zone import Zones
from cardwork.zones.zones import discard, hands, stack


def climbing_zones(players: int) -> Zones:
    return {
        **hands(players),
        **stack(),
        **discard(),
    }
