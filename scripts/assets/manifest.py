from pathlib import Path
from typing import Final

from cardtable.artwork import PackManifest

MANIFEST: Final[str] = "manifest.json"
INDENT: Final[int] = 2


def write(manifest: PackManifest, into: Path) -> int:
    """State what one pack holds in the directory it landed in, and answer with how many bytes landed.

    A table reads this as it opens and a page reads it as it loads, so the one file a fetch writes last is
    the one both of them are told the pack by.
    """
    body = manifest.model_dump_json(indent=INDENT) + "\n"
    into.mkdir(parents=True, exist_ok=True)
    (into / MANIFEST).write_text(body, encoding="utf-8")
    return len(body)
