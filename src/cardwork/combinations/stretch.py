from dataclasses import dataclass
from typing import Final

from cardwork.cards.rank import Ranks

SHORTEST_STRETCH: Final[int] = 2


@dataclass(frozen=True)
class Stretch:
    """Consecutive ranks a run fills, beside whether it reads its highest rank as its lowest.

    `ranks` ends on the rank the run is topped by, which is what settles one run against another. `low_ace`
    holds for the stretch that begins on the highest rank and continues from the lowest — the A 2 3 4 5 a
    reading admitting the wheel offers, where the ace leads the ranks and reads as the one below the two.
    """

    ranks: Ranks
    low_ace: bool
