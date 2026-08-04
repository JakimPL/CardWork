from enum import StrEnum


class Award(StrEnum):
    """Which end of the standing a match is won at.

    A match is decided on `points`, and whether the seat holding the most of them or the fewest holds the match is
    a rule of the game: one scoring what a seat takes reads `HIGHEST`, and one scoring what it is caught with
    reads `LOWEST`. So an interface names the seat a match belongs to by reading the standing at the end the
    layout points it to, and the direction stays with the game that knows it.
    """

    HIGHEST = "highest"
    LOWEST = "lowest"
