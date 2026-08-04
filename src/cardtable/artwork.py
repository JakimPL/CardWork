from enum import StrEnum

from pydantic import Field

from cardwork.models.base import BaseFrozen


class PackName(StrEnum):
    """The card artwork a table draws with, each named as a fetch and a configuration ask for it.

    `kare` is Susan Kare's Solitaire artwork as it shipped in `cards.dll`, held by Microsoft and fetched here
    for one person to look at on one machine. `svg` is a public-domain drawing per card, a whole jokered deck
    of them and a back besides.
    """

    KARE = "kare"
    SVG = "svg"


class PackManifest(BaseFrozen):
    """What one pack of artwork states about itself, written as it is built and read as a table opens.

    Every card of a pack is named for the rank and the suit it draws, so what a page needs told besides is
    how large a card was written, how it takes to being drawn at another size, whether it carries its own
    edge, and which backs landed with it. That is the whole of the contract between a fetch and a page: the
    files themselves follow from the names, and no table of them travels.
    """

    pack: PackName
    extension: str = Field(min_length=1)
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    pixelated: bool
    cornered: bool
    backs: tuple[str, ...] = Field(min_length=1)
