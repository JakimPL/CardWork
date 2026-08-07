from pathlib import Path
from typing import Self

from pydantic import field_validator
from yaml import safe_load

from cardserver.advanced import Advanced
from cardserver.schemas import Choice
from cardtable.artwork import Artwork
from cardtable.games import GAMES_HELD
from cardtable.service import Service
from cardtable.settings import Settings
from cardwork.models.base import BaseFrozen


class Configuration(BaseFrozen):
    """The whole of one run: the table a company gathers at, what it opens on, how it is drawn, and where it answers.

    The tuning stands beside these as its own section, holding the values a public deployment hardens: how a code
    is guarded and how often an empty lobby is cleared.

    A file states this and a run reads it, which leaves every value a person turns in one place they can read,
    and leaves a command line stating only where a particular run departs from it. Each field is asked for
    outright, so a value the file leaves out is refused as the file is read rather than met as a surprise at the
    table; the port stands at a settled number, since a local run answers at the same address until it is told
    to do otherwise, and a run stating neither seed nor code draws both, so each table deals a match of its own
    behind a hand of ranks of its own.

    The choice is where the gathering opens rather than what it plays: the company settles the game, the seating,
    the decks and the ending among themselves, and this is what stands settled until they do.

    `read` builds one from the file a run is pointed at, which is the only way a configuration arrives.
    """

    table: Settings
    choice: Choice
    artwork: Artwork
    service: Service
    advanced: Advanced

    @field_validator("choice")
    @classmethod
    def _a_choice_names_a_game_this_host_holds(cls, chosen: Choice) -> Choice:
        """The choice as it stands once the game it names is one there are rules for here.

        The seating and the decks are confirmed by those rules as the table is gathered, since what a game is
        played at is the game's own declaration. The name is confirmed here, so a file naming a game this host
        holds nothing for is refused as it is read.

        Raises:
            ValueError: when the game named is one this host holds the rules of nowhere.
        """
        if chosen.game not in GAMES_HELD:
            raise ValueError(f"This host holds the rules of {GAMES_HELD}, and {chosen.game!r} was asked for")

        return chosen

    @classmethod
    def read(cls, path: Path) -> Self:
        """The run one file configures, validated as the configuration it states.

        Raises:
            FileNotFoundError: when no file stands where a run was told to read its configuration from.
            ValidationError: when the file states a run no table opens — a field left out, a value outside
                what a table admits, or a name the configuration holds no field for.
        """
        return cls.model_validate(safe_load(path.read_text(encoding="utf-8")))
