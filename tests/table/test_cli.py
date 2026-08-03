from pathlib import Path
from typing import Final

import pytest
import uvicorn
from fastapi import FastAPI
from pydantic import ValidationError

from cardtable.catalogue import GameName
from cardtable.cli import (
    GRACE_SECONDS,
    HOST,
    PLAYERS,
    PORT,
    ROUNDS,
    SEED,
    TABLE,
    announcement,
    main,
    parser,
    settings_of,
)
from cardtable.hosting import Hosted
from cardtable.paths import INTERFACE
from cardtable.settings import Settings

ASKED: Final[tuple[str, ...]] = (
    "--game",
    "showdown",
    "--players",
    "4",
    "--rounds",
    "5",
    "--seed",
    "11",
    "--table",
    "baize",
    "--grace-seconds",
    "1.5",
)
TOKENS: Final[dict[int, str]] = {0: "token-nought", 1: "token-one"}
BUILT: Final[Path] = Path("frontend") / "dist"


def a_hosted_table(interface: Path | None) -> Hosted:
    """A table in hand as the host hands one over, with a page behind it or none."""
    return Hosted(app=FastAPI(), table=TABLE, tokens=TOKENS, interface=interface)


def test_a_command_line_holding_nothing_opens_a_playable_table() -> None:
    arguments = parser().parse_args([])

    assert settings_of(arguments) == Settings(
        table=TABLE,
        players=PLAYERS,
        rounds=ROUNDS,
        seed=SEED,
        grace_seconds=GRACE_SECONDS,
    )


def test_a_command_line_holding_nothing_names_a_game_to_play() -> None:
    assert GameName(parser().parse_args([]).game) == GameName.PASSING


def test_a_command_line_states_the_table_it_asks_for() -> None:
    arguments = parser().parse_args(list(ASKED))

    assert settings_of(arguments) == Settings(
        table="baize",
        players=4,
        rounds=5,
        seed=11,
        grace_seconds=1.5,
    )


def test_a_command_line_states_the_game_it_asks_for() -> None:
    assert GameName(parser().parse_args(list(ASKED)).game) == GameName.SHOWDOWN


def test_a_game_the_host_holds_no_rules_for_is_turned_away() -> None:
    with pytest.raises(SystemExit):
        parser().parse_args(["--game", "bridge"])


def test_a_seating_no_table_admits_is_turned_away() -> None:
    with pytest.raises(ValidationError):
        settings_of(parser().parse_args(["--players", "1"]))


def test_the_announcement_names_the_address_a_browser_reaches_the_table_at() -> None:
    announced = announcement(a_hosted_table(BUILT), HOST, PORT)

    assert f"http://{HOST}:{PORT}" in announced.splitlines()[0]


def test_the_announcement_names_the_table_and_a_token_for_every_seat() -> None:
    announced = announcement(a_hosted_table(BUILT), HOST, PORT)

    assert TABLE in announced
    assert all(token in announced for token in TOKENS.values())


def test_the_announcement_says_where_a_page_would_be_read_from_when_none_is_built() -> None:
    assert str(INTERFACE) in announcement(a_hosted_table(None), HOST, PORT)


def test_the_announcement_of_a_table_serving_a_page_says_nothing_of_a_build() -> None:
    assert str(INTERFACE) not in announcement(a_hosted_table(BUILT), HOST, PORT)


def test_a_run_opens_the_table_asked_for_and_answers_for_it_at_the_address_given(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The one thing `main` does beyond the pieces above: hand a built application to a server.

    Standing in for the server is what lets the call be read, since a real one would answer until it was
    stopped rather than return.
    """
    listening: dict[str, object] = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **arguments: listening.update(arguments, app=app))

    main(["--table", "baize", "--port", "9001"])

    announced = capsys.readouterr().out
    assert (listening["host"], listening["port"]) == (HOST, 9001)
    assert isinstance(listening["app"], FastAPI)
    assert "baize" in announced
