from typing import Final

RANKS: Final[tuple[str, ...]] = (
    "ace",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "jack",
    "queen",
    "king",
)
SUITS: Final[tuple[str, ...]] = ("clubs", "diamonds", "hearts", "spades")
JOKERS: Final[tuple[str, ...]] = ("black_joker", "red_joker")

BACK: Final[str] = "back"


def face(rank: str, suit: str) -> str:
    """The name one card is written under, which is the rank and the suit as a pack spells them."""
    return f"{rank}_of_{suit}"


def back(design: str) -> str:
    """The name one card back is written under, which is the design it draws."""
    return f"{BACK}_{design}"


def faces() -> tuple[str, ...]:
    """Every card of a jokered deck by name, run suit by suit from the ace to the king and the jokers after.

    A pack writes the same names whichever way it draws them, so a page maps a card to a file once and reads
    every pack through that one mapping.
    """
    return tuple(face(rank, suit) for suit in SUITS for rank in RANKS) + JOKERS
