from dataclasses import replace
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.presentation.scene import SEAT_NAME, Scene

from .demo import (
    AROUND,
    OTHER,
    OWNER,
    SCENE,
    SEATS,
    SHARED,
    a_holding,
    a_layout,
    counts_of,
    gestures_of,
    hand_of,
    slots_of,
)

BIGGER_TABLE: Final[int] = 5
UNSEATED: Final[int] = SEATS


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
    concealed = replace(SCENE, seen=lambda seat: ())
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


def test_a_scene_refuses_a_layout_for_a_seat_the_table_does_not_hold() -> None:
    with pytest.raises(ValidationError, match=f"Seat {UNSEATED} stands outside the {SEATS} seats"):
        SCENE.layout(SEATS, UNSEATED)


def test_a_scene_laying_out_one_seats_zones_under_another_seat_is_refused() -> None:
    astray = replace(SCENE, held=lambda seat: (a_holding(OTHER),))

    with pytest.raises(ValueError, match=f"A zone laid out for seat {OWNER} belongs to it"):
        astray.layout(SEATS, OWNER)


def test_a_scene_sharing_a_zone_that_belongs_to_a_seat_is_refused() -> None:
    with pytest.raises(ValueError, match="A zone the table shares belongs to no seat"):
        Scene(
            title=SCENE.title,
            shared=(a_holding(OWNER),),
            held=slots_of,
            seen=lambda seat: (),
            gestures=gestures_of,
            counts=counts_of,
            readouts=SCENE.readouts,
            phases=SCENE.phases,
        )
