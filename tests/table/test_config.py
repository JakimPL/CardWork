from pathlib import Path
from typing import Final

import pytest
from pydantic import ValidationError

from cardserver.codes import code_in
from cardserver.creation import Creation
from cardtable.config import Configuration
from cardtable.games import GAMES_HELD, GameName
from cardtable.paths import CONFIGURATION
from cardtable.service import PORT, LogLevel
from cardtable.settings import SEEDS

from .config import CONFIGURED, a_config_file, a_file_stating

READINGS: Final[int] = 8
ONE_MATCH: Final[int] = 1
LEAST_SEATED: Final[int] = 2

SPARE: Final[dict[str, object]] = {
    "table": {"name": "baize", "grace_seconds": 0.0},
    "choice": {"game": GameName.SHOWDOWN.value, "players": 2, "decks": 1, "conclusion": {"rounds": 1}},
    "artwork": {"pack": None, "back": "crosshatch"},
    "service": {"host": "0.0.0.0", "advertise": None, "log_level": LogLevel.DEBUG.value},
    "advanced": {
        "turnstile_window": 60.0,
        "wrong_codes_allowed": 10,
        "sweep_seconds": 60.0,
        "democratic": True,
        "creation": Creation.SELF_SERVE.value,
        "stale_seconds": 900.0,
        "idle_seconds": 3600.0,
    },
}


def test_the_repository_states_a_run_a_table_gathers() -> None:
    """The one file every run is configured from, held to the model that reads it."""
    configured = Configuration.read(CONFIGURATION)

    assert configured.choice.game in GAMES_HELD
    assert configured.choice.players >= LEAST_SEATED


def test_a_configuration_reads_back_as_the_run_it_states(tmp_path: Path) -> None:
    assert Configuration.read(a_config_file(tmp_path, CONFIGURED)) == CONFIGURED


def test_a_file_stating_neither_seed_nor_code_nor_port_states_a_run_all_the_same(tmp_path: Path) -> None:
    configured = Configuration.read(a_file_stating(tmp_path, SPARE))

    assert configured.table.seed in range(SEEDS)
    assert code_in(configured.table.code) is not None
    assert configured.service.port == PORT


def test_a_file_stating_no_seed_deals_a_match_of_its_own_every_time_it_is_read(tmp_path: Path) -> None:
    """The seed a table is left to draw stands at whatever the machine's entropy gives it, run after run."""
    path = a_file_stating(tmp_path, SPARE)

    drawn = {Configuration.read(path).table.seed for _ in range(READINGS)}

    assert len(drawn) > ONE_MATCH


def test_a_file_stating_no_code_gathers_behind_a_hand_of_its_own_every_time_it_is_read(tmp_path: Path) -> None:
    path = a_file_stating(tmp_path, SPARE)

    drawn = {Configuration.read(path).table.code for _ in range(READINGS)}

    assert len(drawn) > ONE_MATCH


def test_a_run_told_to_read_a_file_that_stands_nowhere_says_so(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Configuration.read(tmp_path / "elsewhere.yaml")


def test_a_field_a_table_is_gathered_with_is_asked_for_outright(tmp_path: Path) -> None:
    lacking = {**SPARE, "table": {"name": "baize"}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, lacking))


def test_a_field_a_choice_is_settled_by_is_asked_for_outright(tmp_path: Path) -> None:
    lacking = {**SPARE, "choice": {"game": GameName.SHOWDOWN.value, "players": 2, "conclusion": {"rounds": 1}}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, lacking))


def test_a_field_the_tuning_is_held_under_is_asked_for_outright(tmp_path: Path) -> None:
    lacking = {**SPARE, "advanced": {"turnstile_window": 60.0, "wrong_codes_allowed": 10}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, lacking))


def test_a_name_the_configuration_holds_no_field_for_is_turned_away(tmp_path: Path) -> None:
    mistaken = {**SPARE, "grace": 2.0}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, mistaken))


def test_a_game_this_host_holds_the_rules_of_nowhere_is_turned_away_as_the_file_is_read(tmp_path: Path) -> None:
    """What a name is confirmed against here, since the seating and the decks are the game's own to refuse."""
    unheld = {**SPARE, "choice": {"game": "bridge", "players": 2, "decks": 1, "conclusion": {"rounds": 1}}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, unheld))


def test_a_table_seating_nobody_at_all_is_turned_away_as_the_file_is_read(tmp_path: Path) -> None:
    alone = {
        **SPARE,
        "choice": {"game": GameName.SHOWDOWN.value, "players": 0, "decks": 1, "conclusion": {"rounds": 1}},
    }

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, alone))


def test_a_code_reading_as_no_hand_of_ranks_is_turned_away_as_the_file_is_read(tmp_path: Path) -> None:
    unread = {**SPARE, "table": {"name": "baize", "code": "hello", "grace_seconds": 0.0}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, unread))


def test_a_code_of_ranks_that_writes_wider_than_a_code_is_turned_away_as_the_file_is_read(tmp_path: Path) -> None:
    """Six ranks holding the ten write as seven characters, and a code is what a person counts at a glance."""
    overlong = {**SPARE, "table": {"name": "baize", "code": "K10AJ72", "grace_seconds": 0.0}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, overlong))


def test_a_pack_no_fetch_writes_is_turned_away_as_the_file_is_read(tmp_path: Path) -> None:
    unfetched = {**SPARE, "artwork": {"pack": "tarot", "back": "crosshatch"}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, unfetched))


def test_a_log_level_no_server_answers_to_is_turned_away(tmp_path: Path) -> None:
    unheard = {**SPARE, "service": {"host": "127.0.0.1", "advertise": None, "log_level": "whisper"}}

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, unheard))


def test_a_port_no_machine_listens_on_is_turned_away(tmp_path: Path) -> None:
    unreachable = {
        **SPARE,
        "service": {"host": "127.0.0.1", "port": 70000, "advertise": None, "log_level": "info"},
    }

    with pytest.raises(ValidationError):
        Configuration.read(a_file_stating(tmp_path, unreachable))
