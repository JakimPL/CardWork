from enum import StrEnum


class Award(StrEnum):
    """Which end of a standing a match is won at.

    A match is decided on `points`, and whether the seat holding the most of them or the fewest takes it is a rule
    of the game: one scoring what a seat wins reads `HIGHEST`, and one scoring what it is caught with reads
    `LOWEST`. It stands beside the tally it reads, so the rules settling a match on a lead and the interface
    naming the seat that took it ask the same question of the same standing.
    """

    HIGHEST = "highest"
    LOWEST = "lowest"
