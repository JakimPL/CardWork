from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.boards.board import Board
from cardwork.cards.game import GameCard
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.views.position import PositionView
from cardwork.views.project import project_position
from cardwork.zones.zone import ZoneId

from .conftest import (
    ALSO_HELD_BY_ONE,
    ALSO_HELD_BY_ZERO,
    DISCARDED,
    EXPOSED_BY_ZERO,
    HELD_BY_ONE,
    HELD_BY_ZERO,
    SEQ,
)


@dataclass(frozen=True)
class ObserverCase:
    name: str
    observer: int | None
    expected: dict[ZoneId, tuple[GameCard | None, ...]]


CONCEALED_HAND_OF_ONE: Final[tuple[GameCard | None, ...]] = (None, None)
CONCEALED_HAND_OF_ZERO: Final[tuple[GameCard | None, ...]] = (None, None, EXPOSED_BY_ZERO)
CONCEALED_BLIND: Final[tuple[GameCard | None, ...]] = (None,)
CONCEALED_DRAW: Final[tuple[GameCard | None, ...]] = (None, None)
CONCEALED_VAULT: Final[tuple[GameCard | None, ...]] = (None,)
OPEN_DISCARD: Final[tuple[GameCard | None, ...]] = (DISCARDED,)

OBSERVER_CASES: Final[tuple[ObserverCase, ...]] = (
    ObserverCase(
        name="a player reads their own hand and nobody else's",
        observer=0,
        expected={
            "hand:0": (HELD_BY_ZERO, ALSO_HELD_BY_ZERO, EXPOSED_BY_ZERO),
            "hand:1": CONCEALED_HAND_OF_ONE,
            "blind:0": CONCEALED_BLIND,
            "discard": OPEN_DISCARD,
            "draw": CONCEALED_DRAW,
            "vault": CONCEALED_VAULT,
        },
    ),
    ObserverCase(
        name="the seat holding the other hand reads that one instead",
        observer=1,
        expected={
            "hand:0": CONCEALED_HAND_OF_ZERO,
            "hand:1": (HELD_BY_ONE, ALSO_HELD_BY_ONE),
            "blind:0": CONCEALED_BLIND,
            "discard": OPEN_DISCARD,
            "draw": CONCEALED_DRAW,
            "vault": CONCEALED_VAULT,
        },
    ),
    ObserverCase(
        name="a seat holding no cards reads only what lies face up",
        observer=2,
        expected={
            "hand:0": CONCEALED_HAND_OF_ZERO,
            "hand:1": CONCEALED_HAND_OF_ONE,
            "blind:0": CONCEALED_BLIND,
            "discard": OPEN_DISCARD,
            "draw": CONCEALED_DRAW,
            "vault": CONCEALED_VAULT,
        },
    ),
    ObserverCase(
        name="a spectator reads what a seat holding no cards reads",
        observer=None,
        expected={
            "hand:0": CONCEALED_HAND_OF_ZERO,
            "hand:1": CONCEALED_HAND_OF_ONE,
            "blind:0": CONCEALED_BLIND,
            "discard": OPEN_DISCARD,
            "draw": CONCEALED_DRAW,
            "vault": CONCEALED_VAULT,
        },
    ),
)


@pytest.mark.parametrize("case", OBSERVER_CASES, ids=lambda case: case.name)
def test_project_position_narrows_each_zone_to_the_observer_s_entitlement(
    case: ObserverCase, position: Position[GameState]
) -> None:
    view = project_position(position, SEQ, case.observer)

    assert {zone_id: zone.cards for zone_id, zone in view.zones.items()} == case.expected


def test_project_position_keeps_every_zone_at_its_true_length(position: Position[GameState]) -> None:
    view = project_position(position, SEQ, 2)

    assert {zone_id: len(zone.cards) for zone_id, zone in view.zones.items()} == {
        zone_id: len(zone.cards) for zone_id, zone in position.board.zones.items()
    }


def test_project_position_leaves_a_concealed_card_at_the_index_it_occupies(position: Position[GameState]) -> None:
    view = project_position(position, SEQ, 1)

    assert view.zones["hand:0"].cards[2] == EXPOSED_BY_ZERO


def test_project_position_carries_the_id_and_owner_of_each_zone(position: Position[GameState]) -> None:
    view = project_position(position, SEQ, 0)

    assert view.zones["hand:1"].id == "hand:1"
    assert view.zones["hand:1"].owner == 1
    assert view.zones["discard"].owner is None


def test_project_position_stamps_the_sequence_it_was_given(position: Position[GameState]) -> None:
    assert project_position(position, SEQ, 0).seq == SEQ


def test_project_position_names_the_observer_it_was_built_for(position: Position[GameState]) -> None:
    assert project_position(position, SEQ, None).observer is None


def test_project_position_carries_the_rules_cursor(position: Position[GameState]) -> None:
    assert project_position(position, SEQ, 0).state == GameState(phase="play", to_act=frozenset({1}))


def test_project_position_projects_an_empty_board_to_an_empty_view() -> None:
    bare: Position[GameState] = Position(
        board=Board(starting_deck=(), zones={}), state=GameState(phase="setup"), players=1
    )

    assert project_position(bare, 0, 0).zones == {}


def test_project_position_round_trips_through_json(position: Position[GameState]) -> None:
    view = project_position(position, SEQ, 0)

    restored = PositionView[GameState].model_validate_json(view.model_dump_json())

    assert restored == view
