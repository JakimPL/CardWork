from typing import Final

from cardwork.presentation import presets
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.spread import Spread
from cardwork.rounds.state import MatchPhase

from .demo import PILE, hand_of

PLACE: Final[int] = 2
OWNER: Final[int] = 0


def test_a_hand_belongs_to_the_seat_holding_it() -> None:
    slot = presets.hand(hand_of(OWNER), "Your hand", seat=OWNER, place=PLACE)

    assert (slot.seat, slot.spread) == (OWNER, Spread.FAN)


def test_a_hand_shows_its_cards_in_place_of_a_count() -> None:
    slot = presets.hand(hand_of(OWNER), "Your hand", seat=OWNER, place=PLACE)

    assert slot.counted is False


def test_a_hand_carries_the_zone_the_word_and_the_place_it_was_given() -> None:
    slot = presets.hand(hand_of(OWNER), "Your hand", seat=OWNER, place=PLACE)

    assert (slot.zone, slot.label, slot.place) == (hand_of(OWNER), "Your hand", PLACE)


def test_a_holding_belongs_to_the_seat_it_is_read_of() -> None:
    slot = presets.holding(hand_of(OWNER), "Hand", seat=OWNER, place=PLACE)

    assert (slot.seat, slot.spread) == (OWNER, Spread.FAN)


def test_a_holding_read_across_the_table_carries_how_many_cards_it_holds() -> None:
    slot = presets.holding(hand_of(OWNER), "Hand", seat=OWNER, place=PLACE)

    assert slot.counted is True


def test_a_hand_and_a_holding_lay_the_same_cards_out_the_same_way() -> None:
    own = presets.hand(hand_of(OWNER), "Your hand", seat=OWNER, place=PLACE)
    across = presets.holding(hand_of(OWNER), "Hand", seat=OWNER, place=PLACE)

    assert (own.zone, own.seat, own.spread, own.place) == (across.zone, across.seat, across.spread, across.place)


def test_a_heap_belongs_to_the_table_the_seats_share() -> None:
    slot = presets.heap(PILE, "Pile", place=PLACE)

    assert (slot.seat, slot.spread) == (None, Spread.STACK)


def test_a_heap_counts_what_lies_in_it() -> None:
    slot = presets.heap(PILE, "Pile", place=PLACE)

    assert slot.counted is True


def test_a_heap_carries_the_zone_the_word_and_the_place_it_was_given() -> None:
    slot = presets.heap(PILE, "Pile", place=PLACE)

    assert (slot.zone, slot.label, slot.place) == (PILE, "Pile", PLACE)


def test_a_match_of_rounds_pauses_where_its_two_reserved_phases_leave_the_table_at_rest() -> None:
    assert presets.match_interludes() == {
        MatchPhase.BETWEEN_ROUNDS: Interlude.ROUND,
        MatchPhase.MATCH_OVER: Interlude.MATCH,
    }
