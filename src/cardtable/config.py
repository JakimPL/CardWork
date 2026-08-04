from pathlib import Path
from typing import Self

from yaml import safe_load

from cardtable.games import GameName
from cardtable.service import Service
from cardtable.settings import Settings
from cardwork.models.base import BaseFrozen


class Configuration(BaseFrozen):
    """The whole of one run: the game played, the table it is played at, and where that table answers.

    A file states this and a run reads it, which leaves every value a person turns in one place they can
    read, and leaves a command line stating only where a particular run departs from it. Each field is asked
    for outright, so a value the file leaves out is refused as the file is read rather than met as a surprise
    at the table; the port stands at a settled number, since a local run answers at the same address until it
    is told to do otherwise, and a run stating no seed draws one, so each table deals a match of its own.

    `read` builds one from the file a run is pointed at, which is the only way a configuration arrives.
    """

    game: GameName
    table: Settings
    service: Service

    @classmethod
    def read(cls, path: Path) -> Self:
        """The run one file configures, validated as the configuration it states.

        Raises:
            FileNotFoundError: when no file stands where a run was told to read its configuration from.
            ValidationError: when the file states a run no table opens — a field left out, a value outside
                what a table admits, or a name the configuration holds no field for.
        """
        return cls.model_validate(safe_load(path.read_text(encoding="utf-8")))
