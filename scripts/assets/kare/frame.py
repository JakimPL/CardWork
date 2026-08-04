from collections.abc import Sequence
from typing import Final

from PIL import Image, ImageChops, ImageDraw

from scripts.assets.kare.cards import BLACK, DRAWN, FULL, GROUND, MASK, NONE, inked

RING: Final[int] = 3


def shared(faces: Sequence[Image.Image]) -> Image.Image:
    """A mask of the marks every face draws alike, which each of them draws over what it says of its own.

    Raises:
        ValueError: when no faces are given and there is nothing they share.
    """
    if not faces:
        raise ValueError("The marks faces share are read off some faces, and none were given")

    marks = inked(faces[0])
    for face in faces[1:]:
        marks = ImageChops.multiply(marks, inked(face))

    return marks


def edging(size: tuple[int, int], ring: int) -> Image.Image:
    """A mask of the band running round the rim of a card, which is where its outline is drawn."""
    band = Image.new(MASK, size, FULL)
    ImageDraw.Draw(band).rectangle((ring, ring, size[0] - ring - 1, size[1] - ring - 1), fill=NONE)
    return band


def blank(faces: Sequence[Image.Image]) -> Image.Image:
    """The card every face is drawn on: the outline it carries and the corners it is rounded at.

    The artwork holds no blank card of its own, so one is read off the faces themselves. A mark standing at
    the rim of all fifty-two is the card, and every mark within the rim is what one card in particular says,
    which is what leaves a joker the room to say something else.
    """
    outline = ImageChops.multiply(shared(faces), edging(faces[0].size, RING))
    card = Image.new(DRAWN, faces[0].size, GROUND)
    card.putalpha(faces[0].getchannel("A"))
    card.paste(Image.new(DRAWN, faces[0].size, BLACK), (0, 0), outline)
    return card
