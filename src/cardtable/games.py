from enum import StrEnum
from typing import Final


class GameName(StrEnum):
    """The games this host puts into service, each named as a person asks for one.

    A name is the whole of what a configuration, a command line and a gathering say about which game is played,
    and the catalogue is where one turns into rules, so a name stated nowhere in this vocabulary is refused
    before a table is opened.
    """

    CLIMBING = "climbing"
    PASSING = "passing"
    SHOWDOWN = "showdown"
    SHEDDING = "shedding"


GAMES_HELD: Final[tuple[str, ...]] = tuple(name.value for name in GameName)
