from typing import Final

import pytest

from cardwork.presentation.fixture import Fixture
from cardwork.presentation.lay import Lay
from cardwork.presentation.setting import Setting
from cardwork.presentation.spread import Spread
from cardwork.zones.family import Family
from cardwork.zones.presets import HAND, HIDDEN
from cardwork.zones.zone import ZoneId

STOCK: Final[ZoneId] = "stock"
HANDS: Final[Family] = Family(name="hand", ordered=False, visibility=HAND)
TRAYS: Final[Family] = Family(name="tray", ordered=True, visibility=HIDDEN)

HEAP: Final[str] = "Stock"
WORD: Final[str] = "Hand"
MINE: Final[str] = "Your hand"
COUNT: Final[str] = "Cards"
SEALED: Final[str] = "Sealed"


def test_a_heap_belongs_to_the_table_the_seats_share() -> None:
    assert Fixture.heap(STOCK, HEAP).zone == STOCK


def test_a_heap_reads_by_the_card_on_top_of_it_and_counts_what_lies_beneath() -> None:
    assert Fixture.heap(STOCK, HEAP).seen == Lay(label=HEAP, spread=Spread.STACK, counted=True)


def test_a_hand_shows_its_cards_to_its_owner_in_place_of_a_count() -> None:
    assert Setting.hand(HANDS, WORD, mine=MINE, tally=COUNT).held == Lay(
        label=MINE,
        spread=Spread.FAN,
        counted=False,
    )


def test_a_hand_read_across_the_table_lies_the_same_way_and_carries_its_size() -> None:
    assert Setting.hand(HANDS, WORD, mine=MINE, tally=COUNT).seen == Lay(
        label=WORD,
        spread=Spread.FAN,
        counted=True,
    )


def test_a_hand_counts_on_the_plaques_under_the_word_the_game_calls_it_by() -> None:
    assert Setting.hand(HANDS, WORD, mine=MINE, tally=COUNT).tally == COUNT


def test_a_hand_stands_at_the_family_it_was_laid_out_for() -> None:
    assert Setting.hand(HANDS, WORD, mine=MINE, tally=COUNT).family == HANDS


def test_a_sealed_place_reads_the_same_way_wherever_it_is_read_from() -> None:
    setting = Setting.sealed(TRAYS, SEALED)

    assert setting.held == setting.seen == Lay(label=SEALED, spread=Spread.SLOT, counted=False)


def test_a_sealed_place_says_what_lies_there_by_the_drawing_of_it() -> None:
    assert Setting.sealed(TRAYS, SEALED).tally == SEALED


def test_a_family_the_table_draws_nowhere_is_still_counted_on_the_plaques() -> None:
    setting = Setting(family=TRAYS, held=None, seen=None, tally=SEALED)

    assert (setting.held, setting.seen, setting.tally) == (None, None, SEALED)


def test_a_family_reaching_a_player_no_way_at_all_lays_out_nothing() -> None:
    with pytest.raises(ValueError, match="reaches a player laid out or counted"):
        Setting(family=TRAYS, held=None, seen=None, tally=None)
