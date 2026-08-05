from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.boards.board import Board
from cardwork.cards.cards import ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS
from cardwork.decks.deck import Deck
from cardwork.decks.decks import to_game_cards
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.zones.family import Family
from cardwork.zones.presets import HIDDEN, PILE
from cardwork.zones.zone import Zone
from cardwork.zones.zones import HANDS

PLAYERS: Final[int] = 2
SEATS: Final[int] = 3
LONGEST: Final[int] = 0
SHORTER: Final[int] = 1
EMPTY_HANDED: Final[int] = 2
TWO_CARDS: Final[int] = 2
ONE_CARD: Final[int] = 1
NO_CARDS: Final[int] = 0
DECK: Final[Deck] = (ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS)
BLINDS: Final[Family] = Family(name="blind", ordered=True, visibility=HIDDEN)


@pytest.fixture(name="position")
def position_fixture() -> Position[GameState]:
    board = Board(starting_deck=(), zones={})
    return Position(board=board, state=GameState(phase="deal", to_act=frozenset({0})), players=PLAYERS)


@pytest.fixture(name="table")
def table_fixture() -> Position[GameState]:
    """A table of three seats holding two cards, one card and none, which is a round drawing to its close."""
    dealt = {
        HANDS.of(LONGEST): to_game_cards((ACE_OF_SPADES, KING_OF_HEARTS), face_down=True),
        HANDS.of(SHORTER): to_game_cards((QUEEN_OF_CLUBS,), face_down=True),
        HANDS.of(EMPTY_HANDED): (),
    }
    zones = {zone_id: zone.with_cards(dealt[zone_id]) for zone_id, zone in HANDS.zones(SEATS).items()}
    board = Board(starting_deck=DECK, zones=zones)
    return Position(board=board, state=GameState(phase="play", to_act=frozenset({LONGEST})), players=SEATS)


def test_with_board_carries_the_state_and_the_seat_count(position: Position[GameState]) -> None:
    extended = position.with_board(
        position.board.with_zones(
            Zone(
                id="draw",
                visibility=PILE,
                ordered=True,
            )
        )
    )

    assert extended.state == position.state
    assert extended.players == PLAYERS
    assert "draw" in extended.board.zones


def test_with_state_carries_the_board_and_the_seat_count(position: Position[GameState]) -> None:
    advanced = position.with_state(GameState(phase="play", to_act=frozenset({1})))

    assert advanced.board == position.board
    assert advanced.players == PLAYERS
    assert advanced.state.phase == "play"


def test_with_state_leaves_the_position_it_was_called_on_intact(position: Position[GameState]) -> None:
    position.with_state(GameState(phase="play"))

    assert position.state.phase == "deal"


def test_position_requires_at_least_one_seat() -> None:
    with pytest.raises(ValidationError):
        Position(board=Board(starting_deck=(), zones={}), state=GameState(phase="deal"), players=0)


def test_the_seats_of_a_table_run_in_the_order_it_is_read_round(table: Position[GameState]) -> None:
    assert tuple(table.seats) == (LONGEST, SHORTER, EMPTY_HANDED)


def test_counts_reads_how_many_cards_each_seat_holds_in_seat_order(table: Position[GameState]) -> None:
    assert table.counts(HANDS) == (TWO_CARDS, ONE_CARD, NO_CARDS)


def test_held_reads_the_cards_each_seat_holds_in_seat_order(table: Position[GameState]) -> None:
    assert table.held(HANDS) == ((ACE_OF_SPADES, KING_OF_HEARTS), (QUEEN_OF_CLUBS,), ())


def test_holding_reads_the_seats_still_carrying_a_card(table: Position[GameState]) -> None:
    assert table.holding(HANDS) == frozenset({LONGEST, SHORTER})


def test_fewest_reads_the_seat_left_holding_the_least(table: Position[GameState]) -> None:
    assert table.fewest(HANDS) == frozenset({EMPTY_HANDED})


def test_fewest_reads_every_seat_standing_as_short_as_the_shortest(table: Position[GameState]) -> None:
    emptied = table.with_board(table.board.with_zones(table.board.zone(HANDS.of(SHORTER)).with_cards(())))

    assert emptied.fewest(HANDS) == frozenset({SHORTER, EMPTY_HANDED})


def test_a_reading_names_the_family_the_table_stands_the_zones_of(table: Position[GameState]) -> None:
    with pytest.raises(KeyError, match="Unknown zone"):
        table.counts(BLINDS)
