from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path

from cardtable.artwork import PackManifest, PackName
from cardtable.paths import ASSETS
from scripts.assets import vector
from scripts.assets.kare import building
from scripts.assets.kare.cards import SCALE
from scripts.assets.manifest import write


def build(pack: PackName, root: Path, *, scale: int, refresh: bool) -> PackManifest:
    """Put one whole pack on disk under the name it is asked for, and state what landed there."""
    match pack:
        case PackName.KARE:
            return building.build(root, scale=scale, refresh=refresh)

        case PackName.SVG:
            return vector.build(root, refresh=refresh)


def parser() -> ArgumentParser:
    """The packs a run builds and where they land, each standing at something usable until it is given."""
    arguments = ArgumentParser(
        prog="assets",
        description="Build card artwork for local play. Nothing fetched here belongs in the repository.",
    )
    arguments.add_argument(
        "--pack",
        action="append",
        choices=tuple(pack.value for pack in PackName),
        help="which artwork to build, given once per pack (every pack by default)",
    )
    arguments.add_argument("--into", type=Path, default=ASSETS, help="the directory the packs land in")
    arguments.add_argument("--scale", type=int, default=SCALE, help="how many times as large pixel artwork is drawn")
    arguments.add_argument("--refresh", action="store_true", help="fetch every file afresh, in place of skipping")
    return arguments


def main(argv: Sequence[str] | None = None) -> None:
    """Build the artwork asked for, and say what each pack holds and where it landed."""
    arguments = parser().parse_args(argv)
    asked = tuple(PackName(name) for name in arguments.pack) if arguments.pack else tuple(PackName)
    root = Path(arguments.into)

    print(f"Building {', '.join(asked)} into {root}")
    for pack in asked:
        manifest = build(pack, root, scale=arguments.scale, refresh=arguments.refresh)
        write(manifest, root / pack)
        print(f"{pack}: {manifest.width}x{manifest.height} a card, {len(manifest.backs)} back(s)")


if __name__ == "__main__":
    main()
