import pytest
from pydantic import ValidationError

from cardwork.boards.board import Board
from cardwork.zones.presets import PILE
from cardwork.zones.zone import Zone


def test_validate_board_accepts_the_zones_holding_the_starting_deck(board: Board) -> None:
    board.validate_board()


def test_validate_board_rejects_a_vanished_card(board: Board, hand: Zone) -> None:
    short_of_one = board.with_zones(hand.model_copy(update={"cards": hand.cards[:1]}))

    with pytest.raises(ValueError, match="differing from the starting deck"):
        short_of_one.validate_board()


def test_with_zones_leaves_the_board_it_was_called_on_intact(board: Board, hand: Zone) -> None:
    emptied = board.with_zones(hand.model_copy(update={"cards": ()}))

    assert emptied.zone("hand:0").cards == ()
    assert board.zone("hand:0").cards == hand.cards


def test_with_zones_files_a_zone_the_board_had_yet_to_hold(board: Board) -> None:
    extended = board.with_zones(Zone(id="discard", visibility=PILE))

    assert extended.zone("discard").cards == ()


def test_board_requires_each_zone_to_be_filed_under_its_own_id() -> None:
    zone = Zone(id="hand:0", owner=0, visibility=PILE)

    with pytest.raises(ValidationError, match="filed under a key other than their own id"):
        Board(starting_deck=(), zones={"draw": zone})


def test_zone_names_the_ids_the_board_does_hold(board: Board) -> None:
    with pytest.raises(KeyError, match="Unknown zone"):
        board.zone("meld")
