from inspect import signature

from cardserver.protocol import Presentation, Table
from cardwork.games.game import Game
from cardwork.presentation.scene import Scene


def test_a_game_commits_a_move_the_way_the_port_asks_for_it() -> None:
    assert signature(Game.submit) == signature(Table.submit)


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
