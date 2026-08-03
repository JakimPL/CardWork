from argparse import ArgumentParser
from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Final
from urllib.request import urlopen

from cardtable.paths import ASSETS

TIMEOUT: Final[float] = 30.0

KARE_SHEET: Final[str] = "https://raw.githubusercontent.com/zeke/solitaire/main/cards.png"
SVG_CARDS: Final[str] = "https://raw.githubusercontent.com/hayeah/playing-cards-assets/master/svg-cards"

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

SHEET: Final[str] = "cards.png"
COLUMNS: Final[int] = 13
ROWS: Final[int] = 4
CARD_WIDTH: Final[int] = 71
CARD_HEIGHT: Final[int] = 96


class Pack(StrEnum):
    """The card artwork a local run fetches, each named as it is asked for on the command line.

    `kare` is Susan Kare's Solitaire artwork as it shipped in `cards.dll`, held by Microsoft and fetched
    here for one person to look at on one machine. `svg` is a public-domain drawing per card, which covers
    the two jokers a jokered deck deals and the sheet holds no face for.
    """

    KARE = "kare"
    SVG = "svg"


def kare_files() -> Mapping[str, str]:
    """The single sprite sheet the Solitaire faces arrive as, addressed by row and column.

    The sheet runs 13 columns from ace to king across 4 rows of ♣ ♦ ♥ ♠, each card 71 by 96, which is what
    lets a face be drawn as one background offset and no image work at all.
    """
    return {SHEET: KARE_SHEET}


def svg_files() -> Mapping[str, str]:
    """One drawing per card of a jokered deck, each named for the rank and suit it draws."""
    faces = {f"{rank}_of_{suit}.svg": f"{SVG_CARDS}/{rank}_of_{suit}.svg" for suit in SUITS for rank in RANKS}
    jokers = {f"{joker}.svg": f"{SVG_CARDS}/{joker}.svg" for joker in JOKERS}
    return faces | jokers


def files_of(pack: Pack) -> Mapping[str, str]:
    """Where each file of one pack is fetched from, under the name it takes on disk."""
    match pack:
        case Pack.KARE:
            return kare_files()

        case Pack.SVG:
            return svg_files()


def fetch(url: str, into: Path) -> int:
    """Fetch one file to a path, making the directories above it, and answer with how many bytes landed."""
    with urlopen(url, timeout=TIMEOUT) as answer:
        body: bytes = answer.read()

    into.parent.mkdir(parents=True, exist_ok=True)
    into.write_bytes(body)
    return len(body)


def fetch_pack(pack: Pack, root: Path, *, refresh: bool) -> int:
    """Fetch every file of one pack into a directory of its own, and answer with how many were fetched.

    A file already on disk is left as it is, so a run after a run costs nothing; `refresh` fetches each one
    afresh where an upstream has moved.
    """
    fetched = 0
    for name, url in sorted(files_of(pack).items()):
        into = root / pack / name
        if into.exists() and not refresh:
            continue

        print(f"  {pack}/{name}  {fetch(url, into)} bytes")
        fetched += 1

    return fetched


def parser() -> ArgumentParser:
    """The packs a run fetches and where they land, each standing at something usable until it is given."""
    arguments = ArgumentParser(
        prog="assets",
        description="Fetch card artwork for local play. Nothing fetched here belongs in the repository.",
    )
    arguments.add_argument(
        "--pack",
        action="append",
        choices=tuple(pack.value for pack in Pack),
        help="which artwork to fetch, given once per pack (every pack by default)",
    )
    arguments.add_argument("--into", type=Path, default=ASSETS, help="the directory the packs land in")
    arguments.add_argument("--refresh", action="store_true", help="fetch every file afresh, in place of skipping")
    return arguments


def main(argv: Sequence[str] | None = None) -> None:
    """Fetch the artwork asked for, and say what landed where."""
    arguments = parser().parse_args(argv)
    asked = tuple(Pack(name) for name in arguments.pack) if arguments.pack else tuple(Pack)
    root = Path(arguments.into)

    print(f"Fetching {', '.join(asked)} into {root}")
    for pack in asked:
        fetched = fetch_pack(pack, root, refresh=arguments.refresh)
        print(f"{pack}: {fetched} file(s) fetched, {len(files_of(pack))} in hand")


if __name__ == "__main__":
    main()
