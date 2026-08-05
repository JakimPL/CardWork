from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.boards.board import Board
from cardwork.cards.cards import ACE_OF_SPADES, KING_OF_HEARTS, TWO_OF_CLUBS
from cardwork.cards.game import GameCard
from cardwork.exceptions import GameValidationError, LogicError
from cardwork.zones.presets import PILE
from cardwork.zones.zone import Zone, ZoneId
from tests.cases import Case, descriptions

HELD: Final[ZoneId] = "hand:0"
DRAW: Final[ZoneId] = "draw"
UNKNOWN: Final[ZoneId] = "meld"
ONE_CARD: Final[int] = 1
NO_CARDS: Final[int] = 0
HELD_CARDS: Final[int] = 2
PAST_THE_HAND: Final[int] = HELD_CARDS
MORE_THAN_HELD: Final[int] = HELD_CARDS + ONE_CARD
BELOW_NONE: Final[int] = -1


@dataclass(frozen=True)
class ReadingCase(Case):
    """One reading the board answers, named by the question it puts to a zone."""

    read: Callable[[Board, ZoneId], object]


READINGS: Final[tuple[ReadingCase, ...]] = (
    ReadingCase(description="the cards a zone holds", read=Board.cards),
    ReadingCase(description="how many cards a zone holds", read=Board.count),
    ReadingCase(description="whether a zone holds a card", read=Board.holds),
    ReadingCase(description="the cards at the end of a run", read=lambda board, zone_id: board.top(zone_id, ONE_CARD)),
    ReadingCase(
        description="the cards the places of a move name",
        read=lambda board, zone_id: board.taken(zone_id, frozenset({0})),
    ),
)


def test_cards_reads_a_zone_apart_from_the_face_its_cards_lie_at(board: Board) -> None:
    assert board.cards(HELD) == (ACE_OF_SPADES, KING_OF_HEARTS)


def test_count_reads_how_many_cards_a_zone_holds(board: Board) -> None:
    assert board.count(HELD) == HELD_CARDS
    assert board.count(DRAW) == ONE_CARD


def test_holds_reads_a_zone_still_carrying_a_card(board: Board, hand: Zone) -> None:
    emptied = board.with_zones(hand.with_cards(()))

    assert board.holds(HELD)
    assert not emptied.holds(HELD)


def test_top_reads_the_cards_standing_at_the_end_of_a_run(board: Board) -> None:
    assert board.top(HELD, ONE_CARD) == (KING_OF_HEARTS,)


def test_top_reads_no_cards_where_none_are_asked_for(board: Board) -> None:
    assert board.top(HELD, NO_CARDS) == ()


def test_top_reads_the_whole_run_where_every_card_of_it_is_asked_for(board: Board) -> None:
    assert board.top(HELD, HELD_CARDS) == (ACE_OF_SPADES, KING_OF_HEARTS)


def test_top_refuses_a_count_naming_more_cards_than_a_zone_holds(board: Board) -> None:
    with pytest.raises(LogicError, match=f"holds {HELD_CARDS} cards, and {MORE_THAN_HELD} were read"):
        board.top(HELD, MORE_THAN_HELD)


def test_top_refuses_a_count_below_no_cards(board: Board) -> None:
    with pytest.raises(LogicError, match=f"and {BELOW_NONE} were read"):
        board.top(HELD, BELOW_NONE)


def test_taken_reads_the_cards_the_places_of_a_move_name(board: Board) -> None:
    assert board.taken(HELD, frozenset({1})) == (KING_OF_HEARTS,)


def test_taken_refuses_a_place_lying_past_the_cards_a_zone_holds(board: Board) -> None:
    with pytest.raises(KeyError, match=f"Place {PAST_THE_HAND} lies past the {HELD_CARDS} cards"):
        board.taken(HELD, frozenset({PAST_THE_HAND}))


@pytest.mark.parametrize("case", READINGS, ids=descriptions(READINGS))
def test_every_reading_names_the_ids_the_board_does_hold(case: ReadingCase, board: Board) -> None:
    with pytest.raises(KeyError, match="Unknown zone"):
        case.read(board, UNKNOWN)


def test_validate_board_accepts_the_zones_holding_the_starting_deck(board: Board) -> None:
    board.validate_board()


def test_validate_board_rejects_a_vanished_card(board: Board, hand: Zone) -> None:
    short_of_one = board.with_zones(hand.model_copy(update={"cards": hand.cards[:1]}))

    with pytest.raises(GameValidationError, match="while the starting deck holds"):
        short_of_one.validate_board()


def test_validate_board_rejects_a_card_the_deck_never_held(board: Board, hand: Zone) -> None:
    substituted = board.with_zones(
        hand.model_copy(update={"cards": (GameCard(card=TWO_OF_CLUBS, face_down=True), *hand.cards[1:])})
    )

    with pytest.raises(GameValidationError, match="differing from the starting deck"):
        substituted.validate_board()


def test_with_zones_leaves_the_board_it_was_called_on_intact(board: Board, hand: Zone) -> None:
    emptied = board.with_zones(hand.model_copy(update={"cards": ()}))

    assert emptied.zone("hand:0").cards == ()
    assert board.zone("hand:0").cards == hand.cards


def test_with_zones_files_a_zone_the_board_had_yet_to_hold(board: Board) -> None:
    extended = board.with_zones(
        Zone(
            id="discard",
            visibility=PILE,
            ordered=True,
        )
    )

    assert extended.zone("discard").cards == ()


def test_board_requires_each_zone_to_be_filed_under_its_own_id() -> None:
    zone = Zone(
        id="hand:0",
        owner=0,
        visibility=PILE,
        ordered=False,
    )

    with pytest.raises(ValidationError, match="filed under a key other than their own id"):
        Board(starting_deck=(), zones={"draw": zone})


def test_zone_names_the_ids_the_board_does_hold(board: Board) -> None:
    with pytest.raises(KeyError, match="Unknown zone"):
        board.zone("meld")
