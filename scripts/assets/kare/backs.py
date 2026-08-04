from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Final

from PIL import Image

from scripts.assets.fetching import cached
from scripts.assets.kare.cards import cornered, opened
from scripts.assets.packs import back

ILLUSTRATIONS: Final[str] = "https://archive.org/download/cardback3x9xnt"
BITMAP: Final[str] = "Bitmap"
CROSSHATCH: Final[int] = 53


class KareBack(StrEnum):
    """The backs Solitaire dealt face down, each named as a configuration asks for one and a file is written under."""

    CROSSHATCH = "crosshatch"
    WEAVE_ONE = "weave_one"
    WEAVE_TWO = "weave_two"
    ROBOT = "robot"
    FLOWERS = "flowers"
    VINE_ONE = "vine_one"
    VINE_TWO = "vine_two"
    FISH_ONE = "fish_one"
    FISH_TWO = "fish_two"
    SHELLS = "shells"
    CASTLE = "castle"
    HAND = "hand"


ILLUSTRATED: Final[Mapping[KareBack, int]] = {
    KareBack.WEAVE_ONE: 54,
    KareBack.WEAVE_TWO: 55,
    KareBack.ROBOT: 56,
    KareBack.FLOWERS: 57,
    KareBack.VINE_ONE: 58,
    KareBack.VINE_TWO: 59,
    KareBack.FISH_ONE: 60,
    KareBack.FISH_TWO: 61,
    KareBack.SHELLS: 62,
    KareBack.CASTLE: 63,
    KareBack.HAND: 65,
}


def illustration(design: KareBack, root: Path, *, refresh: bool) -> Image.Image:
    """One illustrated back as it was drawn, fetched from the archive that keeps the bitmaps of it."""
    identifier = ILLUSTRATED[design]
    source = root / f"{BITMAP}{identifier}.bmp"
    return cornered(opened(cached(f"{ILLUSTRATIONS}/{BITMAP}{identifier}.bmp", source, refresh=refresh)))


def backs(held: Mapping[int, bytes], root: Path, *, refresh: bool) -> Mapping[str, Image.Image]:
    """Every back the pack deals face down, under the name of the design it draws.

    The plain crosshatch is held in the library the faces are read out of. The illustrated ones are read from
    an archive of the bitmaps as Windows drew them up to 2000, since the library a fetch reaches is a later
    build whose backs are photographs and whose faces are the ones a hand drew in 1990.
    """
    plain = {back(KareBack.CROSSHATCH): cornered(opened(held[CROSSHATCH]))}
    drawn = {back(design): illustration(design, root, refresh=refresh) for design in ILLUSTRATED}
    return plain | drawn
