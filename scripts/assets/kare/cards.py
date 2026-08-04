from io import BytesIO
from typing import Final

from PIL import Image, ImageChops, ImageDraw

WIDTH: Final[int] = 71
HEIGHT: Final[int] = 96
SCALE: Final[int] = 4

DRAWN: Final[str] = "RGBA"
MASK: Final[str] = "L"
GROUND: Final[tuple[int, int, int, int]] = (255, 255, 255, 255)
NOTHING: Final[tuple[int, int, int, int]] = (0, 0, 0, 0)
BLACK: Final[tuple[int, int, int, int]] = (0, 0, 0, 255)
RED: Final[tuple[int, int, int, int]] = (255, 0, 0, 255)
LIGHTEST: Final[int] = 250
FULL: Final[int] = 255
NONE: Final[int] = 0


def opened(bitmap: bytes) -> Image.Image:
    """One bitmap as a picture drawn over a ground, at the size and in the colours it was written in."""
    with Image.open(BytesIO(bitmap)) as held:
        return held.convert(DRAWN)


def cornered(picture: Image.Image) -> Image.Image:
    """The same picture with the ground outside its rounded corners cut away.

    A card carries its own outline and its own corners, and the ground standing outside them runs to each
    corner of the rectangle it was written in. Cutting from those four corners inwards leaves the card its
    shape, and leaves the white it is printed on wherever the outline encloses it.
    """
    cut = picture.copy()
    for corner in ((0, 0), (cut.width - 1, 0), (0, cut.height - 1), (cut.width - 1, cut.height - 1)):
        ImageDraw.floodfill(cut, corner, NOTHING)

    return cut


def upscaled(picture: Image.Image, scale: int) -> Image.Image:
    """The same picture drawn as many times as large, every pixel of it standing as a square of its own.

    Artwork written a pixel at a time is read a pixel at a time, so each one is repeated whole rather than
    blended with what it stands beside: the edges a hand placed stay where they were placed.
    """
    return picture.resize((picture.width * scale, picture.height * scale), Image.Resampling.NEAREST)


def inked(picture: Image.Image) -> Image.Image:
    """A mask of the marks one picture draws, which are the pixels standing over its ground and darker than it."""
    marks = picture.convert(MASK).point(lambda level: FULL if level < LIGHTEST else NONE)
    return ImageChops.multiply(marks, picture.getchannel("A"))


def trimmed(picture: Image.Image) -> Image.Image:
    """The same picture cut down to the marks it draws, with the ground around them left behind.

    Raises:
        ValueError: when the picture draws no marks at all and there is nothing to cut down to.
    """
    marks = inked(picture).getbbox()
    if marks is None:
        raise ValueError("A picture cut down to its marks draws some, and this one draws none")

    return picture.crop(marks)
