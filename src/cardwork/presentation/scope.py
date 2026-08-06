from enum import StrEnum


class Scope(StrEnum):
    """Whom a field of the cursor speaks about.

    A `TABLE` field holds one value for the whole table — the round in play, the phase, the trump — and reads
    in the line stating where play stands. A `SEAT` field holds one value per seat in seat order, as `points`
    does, and reads on each player's plaque.
    """

    TABLE = "table"
    SEAT = "seat"
