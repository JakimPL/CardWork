from pathlib import Path
from typing import Final

from yaml import safe_dump

from cardserver.advanced import Advanced
from cardserver.creation import Creation
from cardserver.schemas import Choice
from cardtable.admin import Admin
from cardtable.artwork import Artwork
from cardtable.config import Configuration
from cardtable.games import GameName
from cardtable.service import LogLevel, Service
from cardtable.settings import Settings
from cardwork.rounds.conclusion import Conclusion

FILE: Final[str] = "config.yaml"
BACK: Final[str] = "crosshatch"
CODE: Final[str] = "KQAJ72"
SECRET: Final[str] = "overseer"

GLYPHS: Final[Artwork] = Artwork(pack=None, back=BACK)
ADVANCED: Final[Advanced] = Advanced(
    turnstile_window=60.0,
    wrong_codes_allowed=10,
    sweep_seconds=60.0,
    democratic=True,
    creation=Creation.SELF_SERVE,
    capacity=None,
    stale_seconds=900.0,
    idle_seconds=3600.0,
    stream_patience=20.0,
    presence_stands=60.0,
)
ADMIN: Final[Admin] = Admin(secret=SECRET)

CONFIGURED: Final[Configuration] = Configuration(
    table=Settings(name="baize", code=CODE, seed=7, grace_seconds=0.5),
    choice=Choice(
        game=GameName.PASSING.value,
        players=3,
        decks=1,
        conclusion=Conclusion(rounds=2),
    ),
    artwork=GLYPHS,
    service=Service(
        host="127.0.0.1",
        port=9000,
        advertise=None,
        log_level=LogLevel.WARNING,
        forwarded_allow_ips=None,
    ),
    advanced=ADVANCED,
    admin=ADMIN,
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
