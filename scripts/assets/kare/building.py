from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final

from PIL import Image

from cardtable.artwork import PackManifest, PackName
from scripts.assets.fetching import cached
from scripts.assets.kare.backs import KareBack, backs
from scripts.assets.kare.cards import BLACK, HEIGHT, RED, WIDTH, cornered, opened, upscaled
from scripts.assets.kare.frame import blank
from scripts.assets.kare.jokers import joker, pip
from scripts.assets.kare.resources import bitmaps
from scripts.assets.packs import RANKS, SUITS, face

LIBRARY: Final[str] = (
    "https://raw.githubusercontent.com/zeke/solitaire/df766a1c53ecab5369801cf1b56da066f2a55f70/cards.dll"
)
SOURCES: Final[str] = ".sources"
CARDS: Final[str] = "cards.dll"
EXTENSION: Final[str] = "png"

FIRST_FACE: Final[int] = 1
DEUCE: Final[int] = 1

BLACK_JOKER: Final[str] = "black_joker"
RED_JOKER: Final[str] = "red_joker"


def identifier(suit: int, rank: int) -> int:
    """Which bitmap draws one card, the suits held whole and each running from the ace to the king."""
    return FIRST_FACE + suit * len(RANKS) + rank


def faces(held: Mapping[int, bytes]) -> Mapping[str, Image.Image]:
    """Every card of a standard deck as it was drawn, under the name the pack writes it to disk as."""
    return {
        face(rank, suit): cornered(opened(held[identifier(down, across)]))
        for down, suit in enumerate(SUITS)
        for across, rank in enumerate(RANKS)
    }


def jokers(drawn: Sequence[Image.Image], held: Mapping[int, bytes]) -> Mapping[str, Image.Image]:
    """The two jokers, drawn on the card the faces share out of the suit marks the deuces of the deck carry."""
    card = blank(drawn)
    pips = [pip(cornered(opened(held[identifier(down, DEUCE)]))) for down in range(len(SUITS))]
    return {
        BLACK_JOKER: joker(card, pips, BLACK),
        RED_JOKER: joker(card, pips, RED),
    }


def pack(root: Path, *, refresh: bool) -> Mapping[str, Image.Image]:
    """The whole pack at the size it was drawn: every face, the two jokers, and every back.

    The artwork is read out of the sources it shipped in, which are kept beside the packs rather than among
    them, so what a table serves is pictures and the one file stating what they are.
    """
    held = bitmaps(cached(LIBRARY, root / SOURCES / CARDS, refresh=refresh))
    drawn = faces(held)
    return {
        **drawn,
        **jokers(tuple(drawn.values()), held),
        **backs(held, root / SOURCES, refresh=refresh),
    }


def build(root: Path, *, scale: int, refresh: bool) -> PackManifest:
    """Write the whole Kare pack into a directory of its own, and state what landed there.

    Every picture is drawn at the one scale, each pixel standing as a square of its own, so a page reading
    the pack at any size reads the edges a hand placed in 1990.
    """
    into = root / PackName.KARE
    into.mkdir(parents=True, exist_ok=True)
    for name, picture in sorted(pack(root, refresh=refresh).items()):
        upscaled(picture, scale).save(into / f"{name}.{EXTENSION}")

    return PackManifest(
        pack=PackName.KARE,
        extension=EXTENSION,
        width=WIDTH * scale,
        height=HEIGHT * scale,
        pixelated=True,
        cornered=True,
        backs=tuple(design.value for design in KareBack),
    )
