from random import Random
from typing import Final

import pytest

from cardgames.passing.game import PassingGame
from cardgames.passing.rules import HAND_ON_TURN, HAND_SIZE, PassingClaim, declares, next_seat
from cardgames.passing.zones import PILE, STACK, TOP_OF_THE_PILE, cards_of, hand_of
from cardwork.exceptions import IllegalMove, NotYourTurn
from cardwork.moves.actions import Declare, Give, Play, Take
from cardwork.moves.move import Move

from .driving import (
    FIRST_CARD,
    ONE_CARD,
    SEATS,
    SEED,
    every_hand,
    exchange,
    exchange_until_the_pile_runs_out,
    held_by,
    pass_on,
    seat_on_turn,
)

LAST_CARD: Final[int] = -1
TWO_CARDS: Final[int] = 2


def test_an_exchange_lays_the_card_given_up_on_the_stack_and_takes_the_top_of_the_pile(passing: PassingGame) -> None:
    seat = seat_on_turn(passing)
    given_up = held_by(passing, seat)[FIRST_CARD]
    taken = cards_of(passing.board.zone(PILE))[TOP_OF_THE_PILE]
    piled = len(passing.board.zone(PILE).cards)

    exchange(passing, FIRST_CARD)

    assert cards_of(passing.board.zone(STACK)) == (given_up,)
    assert not passing.board.zone(STACK).cards[FIRST_CARD].face_down
    assert held_by(passing, seat)[LAST_CARD] == taken
    assert passing.board.zone(hand_of(seat)).cards[LAST_CARD].face_down
    assert len(held_by(passing, seat)) == HAND_ON_TURN
    assert len(passing.board.zone(PILE).cards) == piled - ONE_CARD
    assert passing.state.swapped is True
    assert passing.state.to_act == frozenset({seat})


def test_a_second_exchange_in_one_turn_is_refused_and_leaves_the_round_as_it_stood(passing: PassingGame) -> None:
    exchange(passing, FIRST_CARD)
    standing, hands, head = passing.state, every_hand(passing), passing.head

    with pytest.raises(IllegalMove, match="exchanges once in a turn"):
        exchange(passing, FIRST_CARD)

    assert passing.state == standing
    assert every_hand(passing) == hands
    assert passing.head == head


def test_an_exchange_with_a_pile_run_out_is_refused_and_leaves_the_round_as_it_stood(two_seats: PassingGame) -> None:
    exchange_until_the_pile_runs_out(two_seats)
    standing, hands, head = two_seats.state, every_hand(two_seats), two_seats.head

    with pytest.raises(IllegalMove, match="pile that has run out"):
        exchange(two_seats, FIRST_CARD)

    assert two_seats.state == standing
    assert every_hand(two_seats) == hands
    assert two_seats.head == head


def test_an_exchange_with_a_zone_other_than_the_pile_is_refused(passing: PassingGame) -> None:
    seat = seat_on_turn(passing)

    with pytest.raises(IllegalMove, match="exchanges with the pile"):
        passing.submit(
            Move(player=seat, action=Take(group=STACK, indices=frozenset({FIRST_CARD}))),
            base_seq=passing.head,
        )


def test_a_pass_hands_the_turn_and_the_fourth_card_to_the_next_seat(passing: PassingGame) -> None:
    seat = seat_on_turn(passing)
    following = next_seat(seat, SEATS)
    passed = held_by(passing, seat)[FIRST_CARD]

    pass_on(passing, FIRST_CARD)

    assert passing.state.to_act == frozenset({following})
    assert passing.state.swapped is False
    assert held_by(passing, following)[LAST_CARD] == passed
    assert passing.board.zone(hand_of(following)).cards[LAST_CARD].face_down
    assert len(held_by(passing, seat)) == HAND_SIZE
    assert len(held_by(passing, following)) == HAND_ON_TURN


def test_a_spent_exchange_stands_beside_a_pass_that_closes_the_turn(passing: PassingGame) -> None:
    seat = seat_on_turn(passing)

    exchange(passing, FIRST_CARD)
    pass_on(passing, FIRST_CARD)

    assert passing.state.to_act == frozenset({next_seat(seat, SEATS)})
    assert passing.state.swapped is False
    assert len(passing.board.zone(STACK).cards) == ONE_CARD


def test_the_turn_travels_round_the_table_from_the_seat_leading_the_round(passing: PassingGame) -> None:
    leader = passing.state.led_by

    turns = [seat_on_turn(passing)]
    for _ in range(SEATS):
        pass_on(passing, FIRST_CARD)
        turns.append(seat_on_turn(passing))

    assert turns == [(leader + place) % SEATS for place in range(SEATS + 1)]


def test_a_pass_to_a_seat_other_than_the_next_is_refused(passing: PassingGame) -> None:
    seat = seat_on_turn(passing)
    skipped = (seat + TWO_CARDS) % SEATS

    with pytest.raises(IllegalMove, match="passes to seat"):
        passing.submit(
            Move(player=seat, action=Give(target_player=skipped, indices=frozenset({FIRST_CARD}))),
            base_seq=passing.head,
        )


def test_naming_two_cards_at_once_is_refused(passing: PassingGame) -> None:
    seat = seat_on_turn(passing)

    with pytest.raises(IllegalMove, match="one card at a time"):
        passing.submit(
            Move(player=seat, action=Take(group=PILE, indices=frozenset({FIRST_CARD, ONE_CARD}))),
            base_seq=passing.head,
        )


def test_naming_a_position_the_hand_does_not_hold_is_refused(passing: PassingGame) -> None:
    seat = seat_on_turn(passing)

    with pytest.raises(IllegalMove, match=f"of a hand holding {HAND_ON_TURN}"):
        passing.submit(
            Move(player=seat, action=Take(group=PILE, indices=frozenset({HAND_ON_TURN}))),
            base_seq=passing.head,
        )


def test_an_intent_this_game_leaves_out_is_refused(passing: PassingGame) -> None:
    seat = seat_on_turn(passing)

    with pytest.raises(IllegalMove, match="exchanges, passes or claims a win"):
        passing.submit(
            Move(player=seat, action=Play(group=STACK, indices=frozenset({FIRST_CARD}))),
            base_seq=passing.head,
        )


def test_a_seat_the_turn_stands_away_from_is_refused(passing: PassingGame) -> None:
    waiting = next_seat(seat_on_turn(passing), SEATS)

    with pytest.raises(NotYourTurn):
        passing.submit(
            Move(player=waiting, action=Give(target_player=next_seat(waiting, SEATS), indices=frozenset({FIRST_CARD}))),
            base_seq=passing.head,
        )


def test_the_moves_listed_are_the_exchanges_the_passes_and_a_claim_the_hand_holds(passing: PassingGame) -> None:
    seat = seat_on_turn(passing)

    moves = passing.legal_moves(passing.position)

    assert all(move.player == seat for move in moves)
    assert len(tuple(move for move in moves if isinstance(move.action, Take))) == HAND_ON_TURN
    assert len(tuple(move for move in moves if isinstance(move.action, Give))) == HAND_ON_TURN
    assert tuple(move.action for move in moves if isinstance(move.action, Declare)) == (
        (Declare(claim=PassingClaim.WIN, indices=frozenset()),) if declares(held_by(passing, seat)) else ()
    )


def test_a_spent_exchange_leaves_the_passes_on_the_list(passing: PassingGame) -> None:
    exchange(passing, FIRST_CARD)

    moves = passing.legal_moves(passing.position)

    assert all(not isinstance(move.action, Take) for move in moves)
    assert len(tuple(move for move in moves if isinstance(move.action, Give))) == HAND_ON_TURN


def test_a_pile_run_out_leaves_the_passes_on_the_list(two_seats: PassingGame) -> None:
    exchange_until_the_pile_runs_out(two_seats)

    moves = two_seats.legal_moves(two_seats.position)

    assert all(not isinstance(move.action, Take) for move in moves)
    assert len(tuple(move for move in moves if isinstance(move.action, Give))) == HAND_ON_TURN


def test_every_move_listed_is_one_the_rules_carry_through(passing: PassingGame) -> None:
    for move in passing.legal_moves(passing.position):
        passing.step(passing.position, move, Random(SEED))

    assert passing.head == passing.journal.head
