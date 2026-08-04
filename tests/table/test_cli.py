from pathlib import Path
from typing import Final

import pytest
import uvicorn
from fastapi import FastAPI
from pydantic import ValidationError

from cardtable.cli import address, announcement, configured, main, parser
from cardtable.config import Configuration
from cardtable.games import GameName
from cardtable.hosting import Hosted
from cardtable.interface import joining
from cardtable.paths import CONFIGURATION, INTERFACE
from cardtable.service import LogLevel, Service
from cardtable.settings import Settings

from .config import CONFIGURED, a_config_file

TABLE: Final[str] = "green-baize"
TOKENS: Final[dict[int, str]] = {0: "token-nought", 1: "token-one"}
BUILT: Final[Path] = Path("frontend") / "dist"
SERVICE: Final[Service] = Service(host="127.0.0.1", port=8000, log_level=LogLevel.INFO)
SETTINGS: Final[Settings] = CONFIGURED.table
SEATING: Final[int] = 4
TITLE_AND_SEED: Final[int] = 2

DEPARTING: Final[tuple[str, ...]] = (
    "--game",
    "showdown",
    "--table",
    "other-baize",
    "--players",
    "4",
    "--rounds",
    "5",
    "--seed",
    "11",
    "--grace-seconds",
    "1.5",
    "--host",
    "0.0.0.0",
    "--port",
    "9001",
    "--log-level",
    "debug",
)

DEPARTED: Final[Configuration] = Configuration(
    game=GameName.SHOWDOWN,
    table=Settings(name="other-baize", players=4, rounds=5, seed=11, grace_seconds=1.5),
    service=Service(host="0.0.0.0", port=9001, log_level=LogLevel.DEBUG),
)


def a_hosted_table(interface: Path | None) -> Hosted:
    """A table in hand as the host hands one over, with a page behind it or none."""
    return Hosted(app=FastAPI(), table=TABLE, tokens=TOKENS, interface=interface)


def reading(path: Path, *given: str) -> Configuration:
    """The run a command line asks for, configured from the file it is pointed at."""
    return configured(parser().parse_args(["--config", str(path), *given]))


def test_a_run_reads_the_configuration_the_repository_states_by_default() -> None:
    assert parser().parse_args([]).config == CONFIGURATION


def test_a_command_line_holding_nothing_opens_the_table_its_file_states(tmp_path: Path) -> None:
    assert reading(a_config_file(tmp_path, CONFIGURED)) == CONFIGURED


def test_a_command_line_states_every_value_a_run_departs_from_its_file_with(tmp_path: Path) -> None:
    assert reading(a_config_file(tmp_path, CONFIGURED), *DEPARTING) == DEPARTED


def test_a_value_a_command_line_leaves_alone_stays_the_configured_one(tmp_path: Path) -> None:
    departed = reading(a_config_file(tmp_path, CONFIGURED), "--players", str(SEATING))

    assert departed.table.players == SEATING
    assert departed.game == CONFIGURED.game
    assert departed.service == CONFIGURED.service
    assert departed.table == CONFIGURED.table.model_copy(update={"players": SEATING})


def test_a_game_the_host_holds_no_rules_for_is_turned_away() -> None:
    with pytest.raises(SystemExit):
        parser().parse_args(["--game", "bridge"])


def test_a_log_level_no_server_answers_to_is_turned_away() -> None:
    with pytest.raises(SystemExit):
        parser().parse_args(["--log-level", "whisper"])


def test_a_seating_no_table_admits_is_turned_away(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        reading(a_config_file(tmp_path, CONFIGURED), "--players", "1")


def test_a_port_no_machine_listens_on_is_turned_away(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        reading(a_config_file(tmp_path, CONFIGURED), "--port", "70000")


def test_a_run_told_to_read_a_file_that_stands_nowhere_says_so(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        reading(tmp_path / "elsewhere.yaml")


def test_the_announcement_names_the_address_a_browser_reaches_the_table_at() -> None:
    announced = announcement(a_hosted_table(BUILT), SETTINGS, SERVICE)

    assert address(SERVICE) in announced.splitlines()[0]


def test_the_announcement_names_the_table_and_a_token_for_every_seat() -> None:
    announced = announcement(a_hosted_table(BUILT), SETTINGS, SERVICE)

    assert TABLE in announced
    assert all(token in announced for token in TOKENS.values())


def test_the_announcement_hands_each_seat_the_address_that_takes_it() -> None:
    """One line per seat, which is the whole of what a player is handed: the address opens the table as them."""
    announced = announcement(a_hosted_table(BUILT), SETTINGS, SERVICE).splitlines()

    assert all(
        joining(address(SERVICE), TABLE, token) in announced[seat + TITLE_AND_SEED] for seat, token in TOKENS.items()
    )


def test_the_announcement_names_the_seed_the_match_was_dealt_from() -> None:
    """A table left to draw its own seed says which one it drew, so the match it dealt can be dealt again."""
    announced = announcement(a_hosted_table(BUILT), SETTINGS, SERVICE)

    assert str(SETTINGS.seed) in announced


def test_the_announcement_hands_a_tab_the_address_that_watches_the_table() -> None:
    announced = announcement(a_hosted_table(BUILT), SETTINGS, SERVICE)

    assert joining(address(SERVICE), TABLE, None) in announced


def test_the_announcement_says_where_a_page_would_be_read_from_when_none_is_built() -> None:
    assert str(INTERFACE) in announcement(a_hosted_table(None), SETTINGS, SERVICE)


def test_the_announcement_of_a_table_serving_a_page_says_nothing_of_a_build() -> None:
    assert str(INTERFACE) not in announcement(a_hosted_table(BUILT), SETTINGS, SERVICE)


def test_a_run_opens_the_table_it_is_configured_for_and_answers_for_it_where_it_was_told_to(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The one thing `main` does beyond the pieces above: hand a built application to a server.

    Standing in for the server is what lets the call be read, since a real one would answer until it was
    stopped rather than return.
    """
    listening: dict[str, object] = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **arguments: listening.update(arguments, app=app))

    main(["--config", str(a_config_file(tmp_path, CONFIGURED)), "--port", "9001"])

    announced = capsys.readouterr().out
    assert (listening["host"], listening["port"]) == (CONFIGURED.service.host, 9001)
    assert listening["log_level"] == CONFIGURED.service.log_level
    assert isinstance(listening["app"], FastAPI)
    assert CONFIGURED.table.name in announced
