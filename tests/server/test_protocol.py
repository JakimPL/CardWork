from collections.abc import Callable, Mapping
from inspect import Parameter, Signature, signature
from typing import Final

import pytest

from cardserver.gathering import Gatherings, GovernedSay, SayPolicy
from cardserver.identity import SeatPolicy, TokenSeats
from cardserver.naming import Named
from cardserver.protocols import Presentation, Table
from cardserver.sessions import InService, TableSession
from cardwork.games.game import Game
from cardwork.presentation.scene import Scene

SERVED: Final[tuple[str, ...]] = (
    "attends",
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


def stated_by(member: Callable[..., object]) -> Signature:
    """The call one member states, with every annotation resolved to the type it names.

    A module holding its annotations as strings states the same call as one holding them as types, so both are
    read the same way here and a port is compared with what satisfies it rather than with how it was written.
    """
    return signature(member, eval_str=True)


def asked_for(member: Callable[..., object]) -> Mapping[str, Parameter]:
    """The arguments one member takes, which is what a widened answer leaves standing."""
    return stated_by(member).parameters


def test_a_game_commits_a_move_the_way_the_port_asks_for_it() -> None:
    assert stated_by(Game.submit) == stated_by(Table.submit)


def test_a_game_arranges_a_zone_the_way_the_port_asks_for_it() -> None:
    assert stated_by(Game.arrange) == stated_by(Table.arrange)


def test_a_game_settles_the_way_the_port_asks_for_it() -> None:
    assert stated_by(Game.settle) == stated_by(Table.settle)


def test_a_game_projects_a_position_the_way_the_port_asks_for_it() -> None:
    assert stated_by(Game.view) == stated_by(Table.view)


def test_a_game_projects_its_commits_the_way_the_port_asks_for_them() -> None:
    assert stated_by(Game.events) == stated_by(Table.events)


def test_a_game_marks_what_it_has_published_the_way_the_port_asks_for_it() -> None:
    assert stated_by(Game.mark_published) == stated_by(Table.mark_published)


def test_a_game_reports_its_head_the_way_the_port_asks_for_it() -> None:
    assert stated_by(Game.head.fget) == stated_by(Table.head.fget)


def test_a_game_holds_out_its_record_the_way_the_port_asks_for_it() -> None:
    assert stated_by(Game.journal.fget) == stated_by(Table.journal.fget)


def test_a_game_reports_its_seating_the_way_the_port_asks_for_it() -> None:
    assert stated_by(Game.players.fget) == stated_by(Table.players.fget)


def test_a_scene_lays_a_table_out_the_way_the_port_asks_for_it() -> None:
    assert stated_by(Scene.layout) == stated_by(Presentation.layout)


def test_a_named_arrangement_lays_a_table_out_the_way_the_port_asks_for_it() -> None:
    assert stated_by(Named.layout) == stated_by(Presentation.layout)


@pytest.mark.parametrize("policy", [TokenSeats, Gatherings], ids=["seats listed as a table opens", "a gathering"])
def test_a_credential_becomes_a_seat_the_way_the_port_asks_for_it(policy: type[SeatPolicy]) -> None:
    """Both of the ways this server holds a seat answer the one call, since it is the whole of identity here."""
    assert stated_by(policy.seat) == stated_by(SeatPolicy.seat)


def test_a_say_is_confirmed_the_way_the_port_asks_for_it() -> None:
    assert stated_by(GovernedSay.confirm) == stated_by(SayPolicy.confirm)


@pytest.mark.parametrize("member", SERVED)
def test_a_session_is_asked_for_what_a_table_in_service_is_asked_for(member: str) -> None:
    """A table in service answers a route with the cursor's shape left out, and is asked for exactly the rest.

    Only the answers widen, so the arguments stand as the session states them and a route reaches the session
    it holds through the protocol it found it by.
    """
    assert asked_for(getattr(TableSession, member)) == asked_for(getattr(InService, member))
