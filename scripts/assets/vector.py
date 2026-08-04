from collections.abc import Mapping
from pathlib import Path
from typing import Final

from cardtable.artwork import PackManifest, PackName
from scripts.assets.fetching import fetch
from scripts.assets.packs import back, faces

DRAWINGS: Final[str] = "https://raw.githubusercontent.com/hayeah/playing-cards-assets/master/svg-cards"
EXTENSION: Final[str] = "svg"
WIDTH: Final[int] = 167
HEIGHT: Final[int] = 243

ATLAS: Final[str] = "atlas"
ATLAS_BACK: Final[str] = "https://commons.wikimedia.org/wiki/Special:FilePath/Atlas_deck_card_back_blue_and_brown.svg"


def files() -> Mapping[str, str]:
    """Where each drawing of the pack is fetched from, under the name it takes on disk.

    The faces and the jokers are drawn as one deck and are fetched from the one place. The back is drawn by
    another hand and given away as freely, and is fetched from the archive keeping it.
    """
    drawings = {f"{name}.{EXTENSION}": f"{DRAWINGS}/{name}.{EXTENSION}" for name in faces()}
    return drawings | {f"{back(ATLAS)}.{EXTENSION}": ATLAS_BACK}


def build(root: Path, *, refresh: bool) -> PackManifest:
    """Fetch the whole vector pack into a directory of its own, and state what landed there.

    A drawing already on disk is left as it is, so a run after a run costs nothing; `refresh` fetches each one
    afresh where an upstream has moved.
    """
    into = root / PackName.SVG
    into.mkdir(parents=True, exist_ok=True)
    for name, url in sorted(files().items()):
        drawing = into / name
        if drawing.exists() and not refresh:
            continue

        fetch(url, drawing)

    return PackManifest(
        pack=PackName.SVG,
        extension=EXTENSION,
        width=WIDTH,
        height=HEIGHT,
        pixelated=False,
        cornered=True,
        backs=(ATLAS,),
    )
