from pathlib import Path
from typing import Final

import pytest
from pydantic import ValidationError

from cardtable.config import Configuration
from cardtable.games import GameName
from cardtable.paths import CONFIGURATION
from cardtable.service import PORT, LogLevel
from cardtable.settings import SEEDS

from .config import CONFIGURED, a_config_file, a_file_stating

READINGS: Final[int] = 8
ONE_MATCH: Final[int] = 1

SPARE: Final[dict[str, object]] = {
    "game": GameName.SHOWDOWN.value,
    "table": {"name": "baize", "players": 2, "rounds": 1, "grace_seconds": 0.0},
    "service": {"host": "0.0.0.0", "log_level": LogLevel.DEBUG.value},
}


def test_the_repository_states_a_run_a_table_opens() -> None:
    """The one file every run is configured from, held to the model that reads it."""
    configured = Configuration.read(CONFIGURATION)

    assert configured.game in tuple(GameName)
    assert configured.table.players >= 2


def test_a_configuration_reads_back_as_the_run_it_states(tmp_path: Path) -> None:
    assert Configuration.read(a_config_file(tmp_path, CONFIGURED)) == CONFIGURED


def test_a_file_stating_neither_seed_nor_port_states_a_run_all_the_same(tmp_path: Path) -> None:
    configured = Configuration.read(a_file_stating(tmp_path, SPARE))

    assert configured.table.seed in range(SEEDS)
    assert configured.service.port == PORT


def test_a_file_stating_no_seed_deals_a_match_of_its_own_every_time_it_is_read(tmp_path: Path) -> None:
    """The seed a table is left to draw stands at whatever the machine's entropy gives it, run after run."""
    path = a_file_stating(tmp_path, SPARE)

    drawn = {Configuration.read(path).table.seed for _ in range(READINGS)}

    assert len(drawn) > ONE_MATCH


def test_a_run_told_to_read_a_file_that_stands_nowhere_says_so(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Configuration.read(tmp_path / "elsewhere.yaml")


def test_a_field_a_table_is_opened_with_is_asked_for_outright(tmp_path: Path) -> None:
    lacking = {**SPARE, "table": {"name": "baize", "rounds": 1, "grace_seconds": 0.0}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, lacking))


def test_a_name_the_configuration_holds_no_field_for_is_turned_away(tmp_path: Path) -> None:
    mistaken = {**SPARE, "grace": 2.0}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, mistaken))


def test_a_seating_no_table_admits_is_turned_away_as_the_file_is_read(tmp_path: Path) -> None:
    alone = {**SPARE, "table": {"name": "baize", "players": 1, "rounds": 1, "grace_seconds": 0.0}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, alone))


def test_a_log_level_no_server_answers_to_is_turned_away(tmp_path: Path) -> None:
    unheard = {**SPARE, "service": {"host": "127.0.0.1", "log_level": "whisper"}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, unheard))


def test_a_port_no_machine_listens_on_is_turned_away(tmp_path: Path) -> None:
    unreachable = {**SPARE, "service": {"host": "127.0.0.1", "port": 70000, "log_level": "info"}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, unreachable))
