from typing import Final

import pytest

from cardwork.moves.actions import Give
from cardwork.moves.move import Move
from cardwork.presentation.commit import Commit
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.layout import Layout
from cardwork.presentation.scope import Scope
from cardwork.rounds.state import MatchPhase
from tests.cases import descriptions

from .games import CASES, OBSERVERS, PLAYERS, SEATS, LayoutCase

ONE_GESTURE: Final[int] = 1
IDS: Final[list[str]] = descriptions(CASES)
STANDING: Final[str] = "points"
ROUND_AWARD: Final[str] = "round_points"


def made_by(layout: Layout, move: Move) -> tuple[Gesture, ...]:
    """Every gesture of the layout that makes the move, which a layout holds to the one an interface resolves."""
    return tuple(gesture for gesture in layout.gestures if gesture.matches(move.action))


def gesture_for(layout: Layout, move: Move) -> Gesture:
    """The one gesture the move is made with.

    Raises:
        AssertionError: when the layout offers the move no gesture, or offers it two.
    """
    found = made_by(layout, move)
    assert len(found) == ONE_GESTURE, f"{move.action} is made by {found}"
    return found[0]


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("seat", SEATS)
def test_a_seat_reads_its_own_zones_the_seats_around_it_and_the_ones_the_table_shares(
    seat: int,
    case: LayoutCase,
) -> None:
    layout = case.scene.layout(PLAYERS, seat)

    assert len(layout.slots) == case.held + case.seen * (PLAYERS - 1) + case.shared


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("seat", SEATS)
def test_a_seat_reads_the_cards_of_every_seat_at_the_table(seat: int, case: LayoutCase) -> None:
    layout = case.scene.layout(PLAYERS, seat)

    assert {slot.seat for slot in layout.slots if slot.seat is not None} == set(SEATS)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_a_spectator_reads_every_seat_of_the_table_and_makes_no_move(case: LayoutCase) -> None:
    layout = case.scene.layout(PLAYERS, None)

    assert (len(layout.slots), layout.gestures) == (case.seen * PLAYERS + case.shared, ())


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("seat", SEATS)
def test_a_seat_is_offered_the_gestures_a_turn_is_made_of(seat: int, case: LayoutCase) -> None:
    layout = case.scene.layout(PLAYERS, seat)

    assert len(layout.gestures) == case.gestures


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("observer", OBSERVERS)
def test_every_seat_takes_a_plaque_counting_the_zones_it_holds(observer: int | None, case: LayoutCase) -> None:
    layout = case.scene.layout(PLAYERS, observer)

    assert [len(plaque.counts) for plaque in layout.plaques] == [case.counts] * PLAYERS


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_every_phase_the_game_runs_in_is_captioned(case: LayoutCase) -> None:
    layout = case.scene.layout(PLAYERS, None)

    assert set(layout.phases) == set(case.phases)


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("observer", OBSERVERS)
def test_the_phase_the_table_stands_in_is_captioned(observer: int | None, case: LayoutCase) -> None:
    view = case.table().view(observer)
    layout = case.scene.layout(PLAYERS, observer)

    assert view.state.phase in layout.phases


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_a_match_of_rounds_pauses_at_the_close_of_a_round_and_at_the_close_of_the_match(case: LayoutCase) -> None:
    layout = case.scene.layout(PLAYERS, None)

    assert layout.interludes == {
        MatchPhase.BETWEEN_ROUNDS: Interlude.ROUND,
        MatchPhase.MATCH_OVER: Interlude.MATCH,
    }
    assert layout.award is case.award


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_the_round_a_seat_took_reads_beside_the_standing_it_was_added_into(case: LayoutCase) -> None:
    """A round read out as it closes says what each seat took of it, so every game scopes that tally to a seat."""
    layout = case.scene.layout(PLAYERS, None)

    seated = {readout.field for readout in layout.readouts if readout.scope is Scope.SEAT}
    assert {STANDING, ROUND_AWARD} <= seated


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_some_seat_is_offered_a_move_for_a_gesture_to_make(case: LayoutCase) -> None:
    table = case.table()

    assert any(table.view(seat).legal for seat in SEATS)


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("observer", OBSERVERS)
def test_every_move_an_observer_is_offered_is_made_by_one_gesture(observer: int | None, case: LayoutCase) -> None:
    view = case.table().view(observer)
    layout = case.scene.layout(PLAYERS, observer)

    assert {len(made_by(layout, move)) for move in view.legal} <= {ONE_GESTURE}


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("observer", OBSERVERS)
def test_a_gesture_picks_in_a_zone_holding_the_positions_its_move_names(observer: int | None, case: LayoutCase) -> None:
    view = case.table().view(observer)
    layout = case.scene.layout(PLAYERS, observer)

    beyond = tuple(
        move
        for move in view.legal
        if max(move.action.indices) >= len(view.zones[gesture_for(layout, move).picked].cards)
    )
    assert beyond == ()


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("observer", OBSERVERS)
def test_a_gesture_commits_onto_a_zone_the_observer_reads(observer: int | None, case: LayoutCase) -> None:
    view = case.table().view(observer)
    layout = case.scene.layout(PLAYERS, observer)

    targets = tuple(
        gesture.target for move in view.legal if (gesture := gesture_for(layout, move)).commit is Commit.ZONE
    )
    assert all(target in view.zones for target in targets)


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("observer", OBSERVERS)
def test_a_gesture_committing_onto_a_seat_takes_it_from_a_move_naming_one(
    observer: int | None,
    case: LayoutCase,
) -> None:
    view = case.table().view(observer)
    layout = case.scene.layout(PLAYERS, observer)

    onto_a_seat = tuple(move for move in view.legal if gesture_for(layout, move).commit is Commit.SEAT)
    assert all(isinstance(move.action, Give) and move.action.target_player in SEATS for move in onto_a_seat)


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("observer", OBSERVERS)
def test_every_zone_a_slot_lays_out_is_one_the_observer_reads(observer: int | None, case: LayoutCase) -> None:
    view = case.table().view(observer)
    layout = case.scene.layout(PLAYERS, observer)

    assert all(slot.zone in view.zones for slot in layout.slots)


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("observer", OBSERVERS)
def test_every_zone_a_plaque_counts_is_one_the_observer_reads(observer: int | None, case: LayoutCase) -> None:
    view = case.table().view(observer)
    layout = case.scene.layout(PLAYERS, observer)

    counted = tuple(tally.zone for plaque in layout.plaques for tally in plaque.counts)
    assert all(zone in view.zones for zone in counted)


@pytest.mark.parametrize("case", CASES, ids=IDS)
@pytest.mark.parametrize("observer", OBSERVERS)
def test_a_layout_crosses_the_wire_whole(observer: int | None, case: LayoutCase) -> None:
    layout = case.scene.layout(PLAYERS, observer)

    assert Layout.model_validate_json(layout.model_dump_json()) == layout
