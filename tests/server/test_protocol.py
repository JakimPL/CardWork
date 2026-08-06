from collections.abc import Callable, Mapping
from inspect import Parameter, signature
from typing import Final

import pytest

from cardserver.protocol import Presentation, Table
from cardserver.sessions import InService, TableSession
from cardwork.games.game import Game
from cardwork.presentation.scene import Scene

SERVED: Final[tuple[str, ...]] = (
    "reveal",
    "layout",
    "view",
    "events",
    "submit",
    "arrange",
    "watch",
    "drain",
    "close",
)


def asked_for(member: Callable[..., object]) -> Mapping[str, Parameter]:
    """The arguments one member takes, which is what a widened answer leaves standing."""
    return signature(member).parameters


def test_a_game_commits_a_move_the_way_the_port_asks_for_it() -> None:
    assert signature(Game.submit) == signature(Table.submit)


def test_a_game_arranges_a_zone_the_way_the_port_asks_for_it() -> None:
    assert signature(Game.arrange) == signature(Table.arrange)


def test_a_game_settles_the_way_the_port_asks_for_it() -> None:
    assert signature(Game.settle) == signature(Table.settle)


def test_a_game_projects_a_position_the_way_the_port_asks_for_it() -> None:
    assert signature(Game.view) == signature(Table.view)


def test_a_game_projects_its_commits_the_way_the_port_asks_for_them() -> None:
    assert signature(Game.events) == signature(Table.events)


def test_a_game_marks_what_it_has_published_the_way_the_port_asks_for_it() -> None:
    assert signature(Game.mark_published) == signature(Table.mark_published)


def test_a_game_reports_its_head_the_way_the_port_asks_for_it() -> None:
    assert signature(Game.head.fget) == signature(Table.head.fget)


def test_a_game_holds_out_its_record_the_way_the_port_asks_for_it() -> None:
    assert signature(Game.journal.fget) == signature(Table.journal.fget)


def test_a_game_reports_its_seating_the_way_the_port_asks_for_it() -> None:
    assert signature(Game.players.fget) == signature(Table.players.fget)


def test_a_scene_lays_a_table_out_the_way_the_port_asks_for_it() -> None:
    assert signature(Scene.layout) == signature(Presentation.layout)


@pytest.mark.parametrize("member", SERVED)
def test_a_session_is_asked_for_what_a_table_in_service_is_asked_for(member: str) -> None:
    """A table in service answers a route with the cursor's shape left out, and is asked for exactly the rest.

    Only the answers widen, so the arguments stand as the session states them and a route reaches the session
    it holds through the protocol it found it by.
    """
    assert asked_for(getattr(TableSession, member)) == asked_for(getattr(InService, member))
