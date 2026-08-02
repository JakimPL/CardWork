from enum import StrEnum


class Suit(StrEnum):
    SPADE = "♠"
    HEART = "♥"
    CLUB = "♣"
    DIAMOND = "♦"

    @property
    def red(self) -> bool:
        return self in {Suit.HEART, Suit.DIAMOND}
