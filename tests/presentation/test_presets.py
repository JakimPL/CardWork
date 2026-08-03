from typing import Final

from cardwork.presentation import presets
from cardwork.presentation.region import Region
from cardwork.presentation.spread import Spread

from .demo import PILE, hand_of

PLACE: Final[int] = 2
OWNER: Final[int] = 0


def test_a_hand_lies_in_the_region_of_the_seat_holding_it() -> None:
    slot = presets.hand(hand_of(OWNER), "Your hand", place=PLACE)

    assert (slot.region, slot.spread) == (Region.SEAT, Spread.FAN)


def test_a_hand_shows_its_cards_in_place_of_a_count() -> None:
    slot = presets.hand(hand_of(OWNER), "Your hand", place=PLACE)

    assert slot.counted is False


def test_a_hand_carries_the_zone_the_word_and_the_place_it_was_given() -> None:
    slot = presets.hand(hand_of(OWNER), "Your hand", place=PLACE)

    assert (slot.zone, slot.label, slot.place) == (hand_of(OWNER), "Your hand", PLACE)


def test_a_heap_lies_on_the_table_the_seats_share() -> None:
    slot = presets.heap(PILE, "Pile", place=PLACE)

    assert (slot.region, slot.spread) == (Region.TABLE, Spread.STACK)


def test_a_heap_counts_what_lies_in_it() -> None:
    slot = presets.heap(PILE, "Pile", place=PLACE)

    assert slot.counted is True


def test_a_heap_carries_the_zone_the_word_and_the_place_it_was_given() -> None:
    slot = presets.heap(PILE, "Pile", place=PLACE)

    assert (slot.zone, slot.label, slot.place) == (PILE, "Pile", PLACE)
