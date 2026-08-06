from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.layout import Layout
from cardwork.presentation.readout import Readout
from cardwork.presentation.scope import Scope
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.states.award import Award
from cardwork.zones.zone import ZoneId

from .demo import (
    DEALT_FROM,
    GESTURES,
    GIVEN_UP,
    HELD,
    LAID_ON,
    OTHER,
    OWNER,
    PILE,
    PLAQUES,
    READOUTS,
    SCORED,
    SEATS,
    SHARED,
    SLOTS,
    STAGE,
    STANDING,
    a_layout,
    hand_of,
)

UNSEATED: Final[int] = SEATS
UNLAID: Final[ZoneId] = "vault"


def test_a_layout_holds_the_table_it_was_built_for() -> None:
    layout = a_layout()

    assert (layout.observer, layout.players) == (OWNER, SEATS)
    assert layout.slots == SLOTS
    assert layout.gestures == GESTURES


def test_a_layout_for_a_spectator_seats_nobody() -> None:
    assert a_layout(gestures=(), observer=None).observer is None


def test_a_layout_round_trips_through_json() -> None:
    layout = a_layout()

    assert Layout.model_validate_json(layout.model_dump_json()) == layout


def test_a_layout_naming_a_seat_the_table_does_not_hold_is_refused() -> None:
    with pytest.raises(ValidationError, match=f"Seat {UNSEATED} stands outside the {SEATS} seats"):
        a_layout(observer=UNSEATED)


def test_a_layout_laying_one_zone_out_twice_is_refused() -> None:
    twice = Slot(zone=PILE, label="Pile again", seat=None, spread=Spread.SLOT, place=2, counted=True)

    with pytest.raises(ValidationError, match="A zone is laid out once"):
        a_layout(slots=SLOTS + (twice,))


def test_a_layout_naming_a_slot_of_a_seat_the_table_does_not_hold_is_refused() -> None:
    unseated = Slot(zone=UNLAID, label="Vault", seat=UNSEATED, spread=Spread.SLOT, place=0, counted=True)

    with pytest.raises(ValidationError, match=f"A slot belongs to one of the {SEATS} seats or to the table"):
        a_layout(slots=SLOTS + (unseated,))


def test_a_layout_giving_two_slots_of_one_owner_the_same_place_is_refused() -> None:
    shared = Slot(zone=UNLAID, label="Vault", seat=None, spread=Spread.SLOT, place=DEALT_FROM.place, counted=True)

    with pytest.raises(ValidationError, match="A place among one owner's slots holds one slot"):
        a_layout(slots=SLOTS + (shared,))


def test_a_layout_giving_two_owners_the_same_place_is_accepted() -> None:
    layout = a_layout()

    assert {(slot.seat, slot.place) for slot in layout.slots} >= {(OWNER, 0), (OTHER, 0), (None, 0)}


def test_a_layout_leaving_a_seat_without_a_plaque_is_refused() -> None:
    with pytest.raises(ValidationError, match=f"Each of the {SEATS} seats takes one plaque"):
        a_layout(plaques=PLAQUES[:-1])


def test_a_layout_giving_one_seat_two_plaques_is_refused() -> None:
    with pytest.raises(ValidationError, match=f"Each of the {SEATS} seats takes one plaque"):
        a_layout(plaques=PLAQUES + (PLAQUES[0],))


def test_a_layout_stating_one_kind_and_group_twice_is_refused() -> None:
    same = Gesture(
        kind=ActionKind.TAKE,
        group=PILE,
        picked=hand_of(OWNER),
        commit=Commit.ZONE,
        target=PILE,
        caption="Exchange again",
    )

    with pytest.raises(ValidationError, match="A move matches one gesture"):
        a_layout(gestures=GESTURES + (same,))


def test_a_layout_matching_every_group_of_a_kind_beside_one_of_them_is_refused() -> None:
    every = Gesture(
        kind=ActionKind.TAKE,
        group=None,
        picked=hand_of(OWNER),
        commit=Commit.ZONE,
        target=PILE,
        caption="Exchange with anything",
    )

    with pytest.raises(ValidationError, match="A gesture over every group of a kind stands alone"):
        a_layout(gestures=GESTURES + (every,))


def test_a_layout_picking_from_a_zone_it_lays_out_nowhere_is_refused() -> None:
    unreachable = Gesture(
        kind=ActionKind.PLAY,
        group=None,
        picked=UNLAID,
        commit=Commit.ZONE,
        target=PILE,
        caption="Play from the vault",
    )

    with pytest.raises(ValidationError, match="A zone picked from takes a slot of its own"):
        a_layout(gestures=GESTURES + (unreachable,))


def test_a_layout_committing_onto_a_zone_it_lays_out_nowhere_is_refused() -> None:
    unreachable = Gesture(
        kind=ActionKind.PLAY,
        group=None,
        picked=hand_of(OWNER),
        commit=Commit.ZONE,
        target=UNLAID,
        caption="Play into the vault",
    )

    with pytest.raises(ValidationError, match="A zone committed onto takes a slot of its own"):
        a_layout(gestures=GESTURES + (unreachable,))


def test_a_layout_holding_a_gesture_made_in_no_zone_lays_out_nothing_for_it() -> None:
    """A pass names no card and no place, so it reaches a player by its caption rather than by a zone."""
    layout = a_layout(gestures=GESTURES + (GIVEN_UP,))

    assert (layout.gestures[-1].picked, layout.gestures[-1].target) == (None, None)


def test_a_layout_committing_onto_a_seat_names_no_zone_to_lay_out() -> None:
    assert a_layout(slots=(HELD, DEALT_FROM, LAID_ON)).gestures[-1].commit is Commit.SEAT


def test_a_layout_reading_one_field_twice_is_refused() -> None:
    again = Readout(field=STANDING.field, label="Score", scope=Scope.SEAT)

    with pytest.raises(ValidationError, match="A field of the cursor reads once"):
        a_layout(readouts=READOUTS + (again,))


def test_a_layout_reads_the_fields_it_was_given_in_the_order_they_were_stated() -> None:
    assert a_layout().readouts == (STANDING, STAGE)


def test_a_layout_captions_the_phases_it_names() -> None:
    assert a_layout().phases == {"playing": "Your turn", "scored": "Round scored"}


def test_a_layout_names_the_phases_play_pauses_at_and_the_end_a_match_is_won_at() -> None:
    layout = a_layout()

    assert layout.interludes == {SCORED: Interlude.ROUND}
    assert layout.award is Award.LOWEST


def test_a_layout_pausing_at_a_phase_it_captions_nowhere_is_refused() -> None:
    with pytest.raises(ValidationError, match="A phase play pauses at is captioned like any other"):
        a_layout(interludes={"vanished": Interlude.MATCH})


def test_a_layout_pausing_at_no_phase_at_all_is_accepted() -> None:
    """A game running its rounds together pauses nowhere, which the vocabulary states as pausing at nothing."""
    assert a_layout(interludes={}).interludes == {}


def test_a_layout_tallies_a_zone_it_lays_out_nowhere() -> None:
    """A plaque counts another seat's hand, which a table drawing only its own cards holds no slot for."""
    layout = a_layout(slots=(HELD,) + SHARED)
    tallied = {tally.zone for plaque in layout.plaques for tally in plaque.counts}

    assert hand_of(OTHER) in tallied
    assert hand_of(OTHER) not in {slot.zone for slot in layout.slots}
