from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.making import Making
from cardwork.presentation.readout import Readout
from cardwork.presentation.scene import SEAT_NAME
from cardwork.presentation.scope import Scope
from cardwork.presentation.setting import Setting
from cardwork.states.state import GameState
from cardwork.zones.family import Family
from cardwork.zones.presets import HIDDEN
from cardwork.zones.zones import HANDS

from .demo import (
    AROUND,
    AWARD,
    INTERLUDES,
    MAKINGS,
    OTHER,
    OWNER,
    PILE,
    READOUTS,
    SCENE,
    SEATS,
    SHARED,
    a_holding,
    a_layout,
    a_scene,
    counts_of,
    gestures_of,
    hand_of,
    slots_of,
)

BIGGER_TABLE: Final[int] = 5
UNSEATED: Final[int] = SEATS
FIRST: Final[int] = 0
SECOND: Final[int] = 1
SETTLED: Final[str] = "settled"

TRAYS: Final[Family] = Family(name="tray", ordered=True, visibility=HIDDEN)
SEALED_PLACE: Final[Setting] = Setting.sealed(TRAYS, "Sealed")
COUNTED_ALONE: Final[Setting] = Setting(family=HANDS, held=SCENE.seated[FIRST].held, seen=None, tally="Held")

EXCHANGING_AGAIN: Final[Making] = Making(
    kind=ActionKind.TAKE,
    group=PILE,
    picked=HANDS,
    commit=Commit.ZONE,
    target=PILE,
    caption="Exchange with the pile again",
)
SEALING: Final[Making] = Making(
    kind=ActionKind.PLAY,
    group=TRAYS,
    picked=TRAYS,
    commit=Commit.ZONE,
    target=PILE,
    caption="Seal a card the scene lays out nowhere",
)
STANDING_AGAIN: Final[Readout] = Readout.of(GameState, "points", "Score", scope=Scope.SEAT)


def test_a_scene_laid_out_for_a_seat_is_the_layout_of_that_seat() -> None:
    assert SCENE.layout(SEATS, OWNER) == a_layout()


def test_a_scene_lays_out_the_zones_of_the_seat_it_is_read_at() -> None:
    layout = SCENE.layout(SEATS, OTHER)

    assert tuple(slot for slot in layout.slots if slot.seat == OTHER) == slots_of(OTHER)


def test_a_scene_lays_out_the_seats_around_the_observer_as_the_table_reads_them() -> None:
    layout = SCENE.layout(SEATS, OWNER)

    assert layout.slots == slots_of(OWNER) + AROUND + SHARED


def test_a_scene_gathers_the_seats_around_the_observer_in_the_order_they_sit() -> None:
    layout = SCENE.layout(SEATS, OTHER)

    assert [slot.seat for slot in layout.slots] == [OTHER, 0, 1, None, None]


def test_a_scene_offers_the_gestures_of_the_seat_it_is_read_at() -> None:
    layout = SCENE.layout(SEATS, OTHER)

    assert layout.gestures == gestures_of(OTHER)


def test_a_spectator_reads_every_seat_as_the_rest_of_the_table_does() -> None:
    layout = SCENE.layout(SEATS, None)

    assert layout.slots == tuple(a_holding(seat) for seat in range(SEATS)) + SHARED


def test_a_spectator_makes_no_move() -> None:
    layout = SCENE.layout(SEATS, None)

    assert layout.gestures == ()


def test_every_seat_takes_a_plaque_named_by_where_it_sits() -> None:
    layout = SCENE.layout(SEATS, OWNER)

    assert [plaque.name for plaque in layout.plaques] == [SEAT_NAME.format(seat=seat) for seat in range(SEATS)]


def test_a_plaque_counts_the_zones_of_the_seat_it_belongs_to() -> None:
    layout = SCENE.layout(SEATS, OWNER)

    assert [plaque.counts for plaque in layout.plaques] == [counts_of(seat) for seat in range(SEATS)]


def test_a_scene_drawing_no_cards_for_the_other_seats_leaves_their_size_to_the_plaques() -> None:
    concealed = a_scene(seated=(COUNTED_ALONE,))
    layout = concealed.layout(SEATS, OWNER)

    assert layout.slots == slots_of(OWNER) + SHARED
    assert hand_of(OTHER) in {tally.zone for plaque in layout.plaques for tally in plaque.counts}


def test_a_scene_lays_out_a_table_of_any_size_it_is_read_for() -> None:
    layout = SCENE.layout(BIGGER_TABLE, OWNER)

    assert (len(layout.plaques), layout.players) == (BIGGER_TABLE, BIGGER_TABLE)


def test_a_scene_carries_the_title_the_readouts_and_the_captions_to_every_observer() -> None:
    seated = SCENE.layout(SEATS, OWNER)
    watching = SCENE.layout(SEATS, None)

    assert (seated.title, seated.readouts, seated.phases) == (watching.title, watching.readouts, watching.phases)


def test_a_scene_carries_what_a_match_comes_to_to_every_observer() -> None:
    """Where play pauses and which end of the standing wins are one table's, so every seat reads them alike."""
    seated = SCENE.layout(SEATS, OWNER)
    watching = SCENE.layout(SEATS, None)

    assert (seated.interludes, seated.award) == (INTERLUDES, AWARD)
    assert (watching.interludes, watching.award) == (INTERLUDES, AWARD)


def test_a_scene_refuses_a_layout_for_a_seat_the_table_does_not_hold() -> None:
    with pytest.raises(ValidationError, match=f"Seat {UNSEATED} stands outside the {SEATS} seats"):
        SCENE.layout(SEATS, UNSEATED)


def test_a_scene_lays_a_seats_zones_out_in_the_run_it_states_the_families_in() -> None:
    stated = a_scene(seated=(SCENE.seated[FIRST], SEALED_PLACE))
    layout = stated.layout(SEATS, OWNER)

    assert [(slot.zone, slot.place) for slot in layout.slots if slot.seat == OWNER] == [
        (hand_of(OWNER), FIRST),
        (TRAYS.of(OWNER), SECOND),
    ]


def test_a_family_the_table_draws_nowhere_leaves_the_places_of_the_others_where_they_stand() -> None:
    concealed = a_scene(seated=(COUNTED_ALONE, SEALED_PLACE))
    layout = concealed.layout(SEATS, OTHER)

    assert [(slot.zone, slot.place) for slot in layout.slots if slot.seat == OWNER] == [(TRAYS.of(OWNER), SECOND)]


def test_a_scene_binds_every_move_it_states_to_the_seat_reading_it() -> None:
    layout = SCENE.layout(SEATS, OTHER)

    assert [(gesture.picked, gesture.group) for gesture in layout.gestures] == [
        (hand_of(OTHER), PILE),
        (hand_of(OTHER), None),
    ]


def test_a_scene_stating_two_gestures_for_one_move_is_refused() -> None:
    with pytest.raises(ValidationError, match="A move matches one gesture"):
        a_scene(gestures=MAKINGS + (EXCHANGING_AGAIN,))


def test_a_scene_offering_a_gesture_in_a_zone_it_lays_out_nowhere_is_refused() -> None:
    with pytest.raises(ValidationError, match="A zone a gesture names is one the scene lays out"):
        a_scene(gestures=MAKINGS + (SEALING,))


def test_a_scene_reading_one_field_of_the_cursor_twice_is_refused() -> None:
    with pytest.raises(ValidationError, match="A field of the cursor reads once"):
        a_scene(readouts=READOUTS + (STANDING_AGAIN,))


def test_a_scene_pausing_at_a_phase_it_captions_nowhere_is_refused() -> None:
    with pytest.raises(ValidationError, match="A phase play pauses at is captioned like any other"):
        a_scene(interludes={**INTERLUDES, SETTLED: Interlude.MATCH})
