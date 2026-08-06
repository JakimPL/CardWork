from enum import StrEnum
from pathlib import Path
from typing import Final, Self

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import Field, model_validator

from cardwork.models.base import BaseFrozen

MANIFEST: Final[str] = "manifest.json"
ARTWORK: Final[str] = "/artwork"
MOUNT: Final[str] = "artwork"


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


class Artwork(BaseFrozen):
    """The card artwork one table draws with: the pack it reads, and the back its unread cards lie under.

    A run naming no pack draws every card from the glyphs the page carries on its own, which is what a
    checkout that has fetched nothing reads and what a run wanting plain cards states. The back is named
    plainly, since which designs are on offer is the business of the pack that landed on disk, and a name is
    held to that pack as the table opens.
    """

    pack: PackName | None
    back: str = Field(min_length=1)


class ServedPack(PackManifest):
    """One pack in service: what it states of itself, and which of its backs this table lies its cards under.

    This is the whole of what a page is told as it opens — the size a card was written at, how the artwork
    takes to being drawn at another size, whether it carries its own edge, and the one back every face-down
    card of this table draws.
    """

    back: str = Field(min_length=1)

    @model_validator(mode="after")
    def _the_back_is_one_the_pack_holds(self) -> Self:
        if self.back not in self.backs:
            raise ValueError(f"The {self.pack} pack backs its cards with {self.backs}, and holds no {self.back!r}")

        return self

    @classmethod
    def drawing(cls, manifest: PackManifest, back: str) -> Self:
        """That pack, lying every face-down card of one table under the back named.

        Raises:
            ValidationError: when the pack that landed holds no back of that name, which is a run configured
                for artwork other than the artwork on disk.
        """
        return cls(**manifest.model_dump(), back=back)


def stated(pack: Path) -> PackManifest | None:
    """What the pack in one directory states about itself, and None where no pack landed there.

    Raises:
        ValidationError: when a manifest stands there stating something no pack is read as.
    """
    manifest = pack / MANIFEST
    if not manifest.is_file():
        return None

    return PackManifest.model_validate_json(manifest.read_text(encoding="utf-8"))


def state_artwork(app: FastAPI, served: ServedPack) -> None:
    """Answer for the artwork in service at the one address a page reads it from."""

    @app.get(f"{ARTWORK}/{MANIFEST}")
    async def read_artwork() -> ServedPack:
        """The pack this table draws with, which a page reads once as it opens."""
        return served


def serve_artwork(app: FastAPI, root: Path, artwork: Artwork) -> Path | None:
    """Serve the pack a table draws with from one application, and report where it came from.

    The pictures go out of the same application the table answers on, so a page reaches a card where it
    reached its view. What the pack states travels ahead of them, carrying the back this table chose, and
    that route is registered before the mount so it answers ahead of the file of the same name lying in the
    pack itself.

    Args:
        app: the application the table answers on.
        root: where the packs a fetch writes are kept.
        artwork: the pack this run draws with, and the back it lies its unread cards under.

    Returns:
        The directory being served, and None where a run names no pack or where the pack it names has yet to
        be fetched — that table draws from the glyphs its page carries, which every checkout can do.

    Raises:
        ValidationError: when the pack that landed holds no back of the name the run configured.
    """
    if artwork.pack is None:
        return None

    pack = root / artwork.pack
    manifest = stated(pack)
    if manifest is None:
        return None

    state_artwork(app, ServedPack.drawing(manifest, artwork.back))
    app.mount(ARTWORK, StaticFiles(directory=pack), name=MOUNT)
    return pack
