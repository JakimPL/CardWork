from pathlib import Path
from typing import Final

from yaml import safe_dump

from cardtable.config import Configuration
from cardtable.games import GameName
from cardtable.service import LogLevel, Service
from cardtable.settings import Settings

FILE: Final[str] = "config.yaml"

CONFIGURED: Final[Configuration] = Configuration(
    game=GameName.PASSING,
    table=Settings(name="baize", players=3, rounds=2, seed=7, grace_seconds=0.5),
    service=Service(host="127.0.0.1", port=9000, log_level=LogLevel.WARNING),
)


def a_config_file(root: Path, configuration: Configuration) -> Path:
    """A file stating one configuration, which is where a run reads its own from.

    The configuration is written the way it is read, so a test states what it means in the model and the file
    it comes out as stays that model's own business.
    """
    path = root / FILE
    path.write_text(safe_dump(configuration.model_dump(mode="json")), encoding="utf-8")
    return path


def a_file_stating(root: Path, stated: object) -> Path:
    """A file stating whatever is given, which is how a configuration no run admits reaches one."""
    path = root / FILE
    path.write_text(safe_dump(stated), encoding="utf-8")
    return path
