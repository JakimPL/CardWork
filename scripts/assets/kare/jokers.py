from collections.abc import Sequence
from typing import Final

from PIL import Image, ImageDraw

from scripts.assets.kare.cards import DRAWN, NOTHING, inked, trimmed

PIP: Final[tuple[int, int, int, int]] = (26, 3, 45, 30)
CELL: Final[int] = 15
GAP: Final[int] = 3
ACROSS: Final[int] = 2

INDEX: Final[tuple[int, int]] = (4, 6)
MARK: Final[str] = "#"
STAR: Final[tuple[str, ...]] = (
    "#  #  #",
    " # # # ",
    "  ###  ",
    "#######",
    "  ###  ",
    " # # # ",
    "#  #  #",
)


def pip(deuce: Image.Image) -> Image.Image:
    """The suit mark one deuce draws at its head, cut out of the card and trimmed to the ink.

    Every suit marks its deuce at the one size, so four of them read as a set where the ace of spades stands
    alone at a size of its own. Cutting above the middle takes the upright mark and leaves the rotated one.
    """
    return trimmed(deuce.crop(PIP))


def star(colour: tuple[int, int, int, int]) -> Image.Image:
    """The mark a joker is read by in the corner, drawn a pixel at a time in the colour it was dealt in.

    A card is read by its index, and a joker carries no rank to write there, so it carries the mark the rest
    of the table already calls it by.
    """
    drawn = Image.new(DRAWN, (len(STAR[0]), len(STAR)), NOTHING)
    pen = ImageDraw.Draw(drawn)
    for down, row in enumerate(STAR):
        for across, mark in enumerate(row):
            if mark == MARK:
                pen.point((across, down), colour)

    return drawn


def joker(blank: Image.Image, pips: Sequence[Image.Image], colour: tuple[int, int, int, int]) -> Image.Image:
    """One joker: the card every face is drawn on, the four suits across its middle, and its mark in the corners.

    A joker stands for whichever card a game reads it as, so it draws all four suits at once, each lifted from
    the deuce that marks it. The suits keep the colours they are printed in whichever joker they stand on, and
    the mark in the corner is what says which of the two this is.
    """
    drawn = blank.copy()
    block = CELL * ACROSS + GAP * (ACROSS - 1)
    left = (drawn.width - block) // 2
    top = (drawn.height - block) // 2
    for index, suit in enumerate(pips):
        cell = (left + (index % ACROSS) * (CELL + GAP), top + (index // ACROSS) * (CELL + GAP))
        placed = (cell[0] + (CELL - suit.width) // 2, cell[1] + (CELL - suit.height) // 2)
        drawn.paste(suit, placed, inked(suit))

    mark = star(colour)
    drawn.paste(mark, INDEX, mark)
    drawn.paste(mark, (drawn.width - INDEX[0] - mark.width, drawn.height - INDEX[1] - mark.height), mark)
    return drawn
