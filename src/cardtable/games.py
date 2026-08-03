from enum import StrEnum


class GameName(StrEnum):
    """The games this host puts into service, each named as a person asks for one.

    A name is the whole of what a configuration and a command line say about which game is played, and the
    catalogue is where one turns into rules, so a name stated nowhere in this vocabulary is refused before a
    table is opened.
    """

    PASSING = "passing"
    SHOWDOWN = "showdown"
