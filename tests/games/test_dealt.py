from typing import Final

import pytest

from cardwork.boards.board import Board
from cardwork.cards.cards import ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS
from cardwork.decks.deck import Deck
from cardwork.decks.decks import to_game_cards
from cardwork.exceptions import GameValidationError
from cardwork.games.dealt import confirm_dealt
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.zones.family import Family
from cardwork.zones.presets import HIDDEN
from cardwork.zones.zones import HANDS

SEATS: Final[int] = 3
ON_LEAD: Final[int] = 0
FOLLOWING: Final[int] = 1
LAST: Final[int] = 2
ONE_CARD: Final[int] = 1
LED_WITH: Final[int] = 2
UNSEATED: Final[int] = 7
DECK: Final[Deck] = (ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS)
BLINDS: Final[Family] = Family(name="blind", ordered=True, visibility=HIDDEN)
DEALT: Final[dict[int, int]] = {ON_LEAD: LED_WITH, FOLLOWING: ONE_CARD, LAST: ONE_CARD}


@pytest.fixture(name="table")
def table_fixture() -> Position[GameState]:
    """A table of three seats dealt two cards to the seat on lead, one apiece to the rest, and one blind each."""
    hands = {
        HANDS.of(ON_LEAD): to_game_cards((ACE_OF_SPADES, KING_OF_HEARTS), face_down=True),
        HANDS.of(FOLLOWING): to_game_cards((QUEEN_OF_CLUBS,), face_down=True),
        HANDS.of(LAST): to_game_cards((QUEEN_OF_CLUBS,), face_down=True),
    }
    blinds = {BLINDS.of(seat): to_game_cards((ACE_OF_SPADES,), face_down=True) for seat in range(SEATS)}
    laid = {**hands, **blinds}
    zones = {
        zone_id: zone.with_cards(laid[zone_id])
        for zone_id, zone in {**HANDS.zones(SEATS), **BLINDS.zones(SEATS)}.items()
    }
    return Position(
        board=Board(starting_deck=DECK, zones=zones),
        state=GameState(phase="play", to_act=frozenset({ON_LEAD})),
        players=SEATS,
    )


def test_a_deal_giving_each_seat_the_count_it_is_owed_stands(table: Position[GameState]) -> None:
    confirm_dealt(table, HANDS, DEALT)


def test_one_count_stands_for_every_seat(table: Position[GameState]) -> None:
    confirm_dealt(table, BLINDS, ONE_CARD)


def test_a_seat_holding_another_count_than_the_deal_owes_it_is_named(table: Position[GameState]) -> None:
    with pytest.raises(GameValidationError, match=r"Seats \(0,\) hold a hand of a size other than"):
        confirm_dealt(table, HANDS, ONE_CARD)


def test_every_seat_the_deal_left_short_is_named_at_once(table: Position[GameState]) -> None:
    with pytest.raises(GameValidationError, match=r"Seats \(1, 2\) hold a hand"):
        confirm_dealt(table, HANDS, LED_WITH)


def test_the_family_the_counts_are_read_over_is_the_one_the_refusal_names(table: Position[GameState]) -> None:
    with pytest.raises(GameValidationError, match="hold a blind of a size other than"):
        confirm_dealt(table, BLINDS, LED_WITH)


def test_a_deal_naming_no_count_for_a_seat_in_play_is_refused(table: Position[GameState]) -> None:
    with pytest.raises(KeyError):
        confirm_dealt(table, HANDS, {ON_LEAD: LED_WITH, FOLLOWING: ONE_CARD})


def test_the_seats_in_play_are_what_the_counts_are_read_at(table: Position[GameState]) -> None:
    confirm_dealt(table, HANDS, {**DEALT, UNSEATED: LED_WITH})
