from pathlib import Path
from typing import Final

import pytest
import uvicorn
from fastapi import FastAPI
from pydantic import ValidationError

from cardtable.artwork import Artwork, PackName
from cardtable.cli import address, announcement, configured, main, parser
from cardtable.config import Configuration
from cardtable.games import GameName
from cardtable.hosting import Hosted
from cardtable.interface import joining
from cardtable.paths import ASSETS, CONFIGURATION, INTERFACE
from cardtable.service import LogLevel, Service
from cardtable.settings import Settings
from cardwork.rounds.conclusion import Conclusion

from .config import CONFIGURED, GLYPHS, a_config_file

TABLE: Final[str] = "green-baize"
TOKENS: Final[dict[int, str]] = {0: "token-nought", 1: "token-one"}
BUILT: Final[Path] = Path("frontend") / "dist"
DRAWN: Final[Path] = ASSETS / PackName.KARE
SERVICE: Final[Service] = Service(host="127.0.0.1", port=8000, log_level=LogLevel.INFO)
SETTINGS: Final[Settings] = CONFIGURED.table
KARE: Final[Artwork] = Artwork(pack=PackName.KARE, back="crosshatch")
SEATING: Final[int] = 4
TITLE_AND_SEED: Final[int] = 2
A_LEAD: Final[int] = 3
A_TARGET: Final[int] = 40
A_COUNT: Final[int] = 6

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
    "--pack",
    "svg",
    "--back",
    "atlas",
    "--host",
    "0.0.0.0",
    "--port",
    "9001",
    "--log-level",
    "debug",
)

DEPARTED: Final[Configuration] = Configuration(
    game=GameName.SHOWDOWN,
    table=Settings(name="other-baize", players=4, conclusion=Conclusion(rounds=5), seed=11, grace_seconds=1.5),
    artwork=Artwork(pack=PackName.SVG, back="atlas"),
    service=Service(host="0.0.0.0", port=9001, log_level=LogLevel.DEBUG),
)


def a_hosted_table(artwork: Path | None, interface: Path | None) -> Hosted:
    """A table in hand as the host hands one over, with a pack and a page behind it or neither."""
    return Hosted(app=FastAPI(), table=TABLE, tokens=TOKENS, artwork=artwork, interface=interface)


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
    assert departed.artwork == CONFIGURED.artwork
    assert departed.service == CONFIGURED.service
    assert departed.table == CONFIGURED.table.model_copy(update={"players": SEATING})


def test_a_clause_a_command_line_names_states_how_long_the_match_runs(tmp_path: Path) -> None:
    """A clause given replaces the configured ending whole, so a run asking for a lead runs to that alone."""
    departed = reading(a_config_file(tmp_path, CONFIGURED), "--lead", str(A_LEAD))

    assert departed.table.conclusion == Conclusion(lead=A_LEAD)


def test_a_run_naming_no_clause_at_all_runs_to_the_ending_its_file_states(tmp_path: Path) -> None:
    departed = reading(a_config_file(tmp_path, CONFIGURED), "--players", str(SEATING))

    assert departed.table.conclusion == CONFIGURED.table.conclusion


def test_a_run_naming_two_clauses_ends_on_whichever_arrives_first(tmp_path: Path) -> None:
    departed = reading(a_config_file(tmp_path, CONFIGURED), "--target", str(A_TARGET), "--rounds", str(A_COUNT))

    assert departed.table.conclusion == Conclusion(target=A_TARGET, rounds=A_COUNT)


def test_a_clause_below_the_least_a_match_runs_to_is_turned_away(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        reading(a_config_file(tmp_path, CONFIGURED), "--rounds", "0")


def test_a_run_asking_for_no_pack_draws_the_glyphs_the_page_carries(tmp_path: Path) -> None:
    """The one value a command line states by naming nothing: `none` is how a run turns the artwork off."""
    drawn = a_config_file(tmp_path, CONFIGURED.model_copy(update={"artwork": KARE}))

    assert reading(drawn, "--pack", "none").artwork.pack is None


def test_a_run_naming_a_pack_alone_keeps_the_back_its_file_states(tmp_path: Path) -> None:
    departed = reading(a_config_file(tmp_path, CONFIGURED), "--pack", "kare")

    assert departed.artwork == Artwork(pack=PackName.KARE, back=CONFIGURED.artwork.back)


def test_a_pack_no_fetch_writes_is_turned_away() -> None:
    with pytest.raises(SystemExit):
        parser().parse_args(["--pack", "tarot"])


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
    announced = announcement(a_hosted_table(None, BUILT), SETTINGS, GLYPHS, SERVICE)

    assert address(SERVICE) in announced.splitlines()[0]


def test_the_announcement_names_the_table_and_a_token_for_every_seat() -> None:
    announced = announcement(a_hosted_table(None, BUILT), SETTINGS, GLYPHS, SERVICE)

    assert TABLE in announced
    assert all(token in announced for token in TOKENS.values())


def test_the_announcement_hands_each_seat_the_address_that_takes_it() -> None:
    """One line per seat, which is the whole of what a player is handed: the address opens the table as them."""
    announced = announcement(a_hosted_table(None, BUILT), SETTINGS, GLYPHS, SERVICE).splitlines()

    assert all(
        joining(address(SERVICE), TABLE, token) in announced[seat + TITLE_AND_SEED] for seat, token in TOKENS.items()
    )


def test_the_announcement_names_the_seed_the_match_was_dealt_from() -> None:
    """A table left to draw its own seed says which one it drew, so the match it dealt can be dealt again."""
    announced = announcement(a_hosted_table(None, BUILT), SETTINGS, GLYPHS, SERVICE)

    assert str(SETTINGS.seed) in announced


def test_the_announcement_hands_a_tab_the_address_that_watches_the_table() -> None:
    announced = announcement(a_hosted_table(None, BUILT), SETTINGS, GLYPHS, SERVICE)

    assert joining(address(SERVICE), TABLE, None) in announced


def test_the_announcement_names_the_pack_the_table_draws_with_and_the_back_it_lies_under() -> None:
    announced = announcement(a_hosted_table(DRAWN, BUILT), SETTINGS, KARE, SERVICE)

    assert PackName.KARE in announced
    assert KARE.back in announced


def test_the_announcement_says_where_a_pack_would_stand_when_the_one_asked_for_is_unfetched() -> None:
    """A pack is fetched rather than committed, so a run asking for one that has yet to land says as much."""
    announced = announcement(a_hosted_table(None, BUILT), SETTINGS, KARE, SERVICE)

    assert str(ASSETS) in announced


def test_the_announcement_of_a_table_drawing_its_own_glyphs_says_nothing_of_a_pack() -> None:
    announced = announcement(a_hosted_table(None, BUILT), SETTINGS, GLYPHS, SERVICE)

    assert str(ASSETS) not in announced
    assert GLYPHS.back not in announced


def test_the_announcement_says_where_a_page_would_be_read_from_when_none_is_built() -> None:
    assert str(INTERFACE) in announcement(a_hosted_table(None, None), SETTINGS, GLYPHS, SERVICE)


def test_the_announcement_of_a_table_serving_a_page_says_nothing_of_a_build() -> None:
    assert str(INTERFACE) not in announcement(a_hosted_table(None, BUILT), SETTINGS, GLYPHS, SERVICE)


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
