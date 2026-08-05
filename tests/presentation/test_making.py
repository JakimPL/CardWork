from typing import Final

import pytest

from cardwork.moves.actions import Pass, Play
from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.making import Making
from cardwork.zones.family import Family
from cardwork.zones.presets import HAND, HIDDEN
from cardwork.zones.zone import ZoneId

SEAT: Final[int] = 2
DISCARD: Final[ZoneId] = "discard"
HANDS: Final[Family] = Family(name="hand", ordered=False, visibility=HAND)
TRAYS: Final[Family] = Family(name="tray", ordered=True, visibility=HIDDEN)

SEALING: Final[Making] = Making(
    kind=ActionKind.PLAY,
    group=HANDS,
    picked=HANDS,
    commit=Commit.ZONE,
    target=TRAYS,
    caption="Seal this card from your hand",
)
SHEDDING: Final[Making] = Making(
    kind=ActionKind.DISCARD,
    group=HANDS,
    picked=HANDS,
    commit=Commit.ZONE,
    target=DISCARD,
    caption="Shed these cards as one rank",
)
GIVING: Final[Making] = Making(
    kind=ActionKind.GIVE,
    group=None,
    picked=HANDS,
    commit=Commit.SEAT,
    target=None,
    caption="Pass this card to the next seat",
)
SAYING: Final[Making] = Making(
    kind=ActionKind.PASS,
    group=None,
    picked=None,
    commit=Commit.WORD,
    target=None,
    caption="Give up your turn",
)


def test_a_move_picked_and_committed_within_one_seat_names_that_seats_own_zones() -> None:
    assert SEALING.gesture(SEAT) == Gesture(
        kind=ActionKind.PLAY,
        group=HANDS.name,
        picked=HANDS.of(SEAT),
        commit=Commit.ZONE,
        target=TRAYS.of(SEAT),
        caption="Seal this card from your hand",
    )


def test_a_move_landing_on_a_zone_of_the_table_names_it_at_every_seat() -> None:
    assert SHEDDING.gesture(SEAT).target == DISCARD


def test_a_group_travels_as_the_word_the_intent_carries() -> None:
    assert SHEDDING.gesture(SEAT).group == HANDS.name


def test_a_move_committed_onto_a_player_takes_the_seat_from_the_move() -> None:
    assert GIVING.gesture(SEAT).target is None


def test_a_move_naming_no_card_is_picked_in_no_zone() -> None:
    assert SAYING.gesture(SEAT).picked is None


def test_the_gesture_a_seat_is_offered_makes_the_moves_that_seat_makes() -> None:
    gesture = SEALING.gesture(SEAT)

    assert gesture.matches(Play(group=HANDS.name, indices=frozenset({0})))


def test_a_gesture_stating_no_group_makes_every_move_of_its_kind() -> None:
    gesture = SAYING.gesture(SEAT)

    assert gesture.matches(Pass())


def test_a_move_committing_onto_a_zone_names_the_zone_it_lands_on() -> None:
    with pytest.raises(ValueError, match="committing onto a zone names that zone"):
        Making(
            kind=ActionKind.PLAY,
            group=HANDS,
            picked=HANDS,
            commit=Commit.ZONE,
            target=None,
            caption="Seal this card",
        )


def test_a_move_said_by_its_word_lands_on_no_zone() -> None:
    with pytest.raises(ValueError, match="said by its word lands on no zone, and names zone 'discard'"):
        Making(
            kind=ActionKind.PASS,
            group=None,
            picked=None,
            commit=Commit.WORD,
            target=DISCARD,
            caption="Give up your turn",
        )


def test_a_move_committing_onto_a_seat_names_the_family_it_would_land_on_by_its_word() -> None:
    with pytest.raises(ValueError, match="takes it from the move, and names zone 'tray'"):
        Making(
            kind=ActionKind.GIVE,
            group=None,
            picked=HANDS,
            commit=Commit.SEAT,
            target=TRAYS,
            caption="Pass this card",
        )
