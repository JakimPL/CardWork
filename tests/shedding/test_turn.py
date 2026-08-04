from random import Random
from typing import Final

import pytest

from cardgames.backend.shedding.game import SheddingGame
from cardgames.backend.shedding.rules import NOTHING, ROUND_POINT, SHED_LEAST
from cardgames.backend.shedding.state import SheddingPhase
from cardgames.backend.shedding.zones import HAND, STOCK
from cardwork.cards.cards import (
    EIGHT_OF_CLUBS,
    FIVE_OF_DIAMONDS,
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    FOUR_OF_HEARTS,
    KING_OF_CLUBS,
    NINE_OF_CLUBS,
    SEVEN_OF_DIAMONDS,
    SIX_OF_DIAMONDS,
    THREE_OF_DIAMONDS,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardsOrJokers
from cardwork.effects.fold import fold
from cardwork.exceptions import IllegalMove, NotYourTurn
from cardwork.moves.actions import Discard, Play, Take
from cardwork.moves.move import Move
from cardwork.rounds.seating import next_seat
from cardwork.zones.zone import cards_of, hand_of
from cardwork.zones.zones import DISCARD

from .driving import (
    SEATS,
    SEED,
    a_draw,
    a_shed,
    a_table_of,
    draw,
    every_hand,
    every_zone,
    held_by,
    left_over,
    seat_on_turn,
    stocked,
)

ON_TURN: Final[int] = 0
FOLLOWING: Final[int] = 1
LAST_SEAT: Final[int] = 2
RUN_OUT: Final[int] = 0
A_FEW: Final[int] = 3
LAST_CARD: Final[int] = -1

A_PAIR: Final[CardsOrJokers] = (FIVE_OF_SPADES, FIVE_OF_HEARTS)
A_TRIPLET: Final[CardsOrJokers] = (FIVE_OF_SPADES, FIVE_OF_HEARTS, FIVE_OF_DIAMONDS)
ODD_CARDS: Final[CardsOrJokers] = (TWO_OF_SPADES, SEVEN_OF_DIAMONDS)
MORE_ODD_CARDS: Final[CardsOrJokers] = (THREE_OF_DIAMONDS, FOUR_OF_HEARTS, NINE_OF_CLUBS)
ONE_CARD: Final[CardsOrJokers] = (KING_OF_CLUBS,)


def test_a_draw_takes_the_card_at_the_end_of_the_stock_into_the_hand(shedding: SheddingGame) -> None:
    seat = seat_on_turn(shedding)
    stock = stocked(shedding)
    taken = cards_of(shedding.board.zone(STOCK))[LAST_CARD]
    held = len(held_by(shedding, seat))

    draw(shedding)

    assert held_by(shedding, seat)[LAST_CARD] == taken
    assert shedding.board.zone(hand_of(seat)).cards[LAST_CARD].face_down
    assert len(held_by(shedding, seat)) == held + 1
    assert stocked(shedding) == stock - 1
    assert shedding.state.to_act == frozenset({next_seat(seat, SEATS)})


def test_the_turn_travels_round_the_table_from_the_seat_leading_the_round(shedding: SheddingGame) -> None:
    leader = shedding.state.led_by

    turns = [seat_on_turn(shedding)]
    for _ in range(SEATS):
        draw(shedding)
        turns.append(seat_on_turn(shedding))

    assert turns == [(leader + place) % SEATS for place in range(SEATS + 1)]


def test_a_shed_lays_the_set_face_up_on_the_discard_and_hands_the_turn_on(shedding: SheddingGame) -> None:
    hands = (A_PAIR + ODD_CARDS, MORE_ODD_CARDS, ONE_CARD)
    position = a_table_of(shedding, hands, left_over(hands), ON_TURN)

    laid = shedding.step(position, a_shed(ON_TURN, frozenset({0, 1})), Random(SEED))

    assert cards_of(laid.board.zone(DISCARD)) == A_PAIR
    assert all(not game_card.face_down for game_card in laid.board.zone(DISCARD).cards)
    assert cards_of(laid.board.zone(hand_of(ON_TURN))) == ODD_CARDS
    assert laid.state.phase == SheddingPhase.SHEDDING
    assert laid.state.to_act == frozenset({FOLLOWING})
    laid.board.validate_board()


def test_shedding_two_of_a_triplet_leaves_the_third_of_that_rank_in_hand(shedding: SheddingGame) -> None:
    """The choice a turn carries: the whole of a rank goes down, or a pair of it does and a card is kept back."""
    hands = (A_TRIPLET, MORE_ODD_CARDS, ONE_CARD)
    position = a_table_of(shedding, hands, left_over(hands), ON_TURN)

    laid = shedding.step(position, a_shed(ON_TURN, frozenset({0, 2})), Random(SEED))

    assert cards_of(laid.board.zone(DISCARD)) == (FIVE_OF_SPADES, FIVE_OF_DIAMONDS)
    assert cards_of(laid.board.zone(hand_of(ON_TURN))) == (FIVE_OF_HEARTS,)
    assert laid.state.phase == SheddingPhase.SHEDDING


def test_a_seat_shedding_its_last_cards_goes_out_and_takes_the_round(shedding: SheddingGame) -> None:
    hands = (A_PAIR, MORE_ODD_CARDS, ONE_CARD)
    position = a_table_of(shedding, hands, RUN_OUT, ON_TURN)

    out = shedding.step(position, a_shed(ON_TURN, frozenset({0, 1})), Random(SEED))

    assert cards_of(out.board.zone(hand_of(ON_TURN))) == ()
    assert out.state.phase == SheddingPhase.DECIDED
    assert out.state.winner == ON_TURN
    assert out.state.to_act == frozenset()
    assert out.state.round_points == (ROUND_POINT, NOTHING, NOTHING)


def test_the_moves_listed_are_the_sets_of_the_hand_and_the_draw_beside_them(shedding: SheddingGame) -> None:
    hands = (A_TRIPLET + ONE_CARD, MORE_ODD_CARDS, ODD_CARDS)
    position = a_table_of(shedding, hands, A_FEW, ON_TURN)

    moves = shedding.legal_moves(position)

    assert all(move.player == ON_TURN for move in moves)
    assert {frozenset(move.action.indices) for move in moves if isinstance(move.action, Discard)} == {
        frozenset({0, 1}),
        frozenset({0, 2}),
        frozenset({1, 2}),
        frozenset({0, 1, 2}),
    }
    assert tuple(move.action.indices for move in moves if isinstance(move.action, Take)) == (frozenset({A_FEW - 1}),)


def test_a_stock_run_out_leaves_the_sets_of_the_hand_on_the_list(shedding: SheddingGame) -> None:
    hands = (A_PAIR + ODD_CARDS, MORE_ODD_CARDS, ONE_CARD)
    position = a_table_of(shedding, hands, RUN_OUT, ON_TURN)

    moves = shedding.legal_moves(position)

    assert all(isinstance(move.action, Discard) for move in moves)
    assert tuple(move.action.indices for move in moves) == (frozenset({0, 1}),)


def test_a_seat_holding_no_set_with_the_stock_run_out_is_offered_nothing(shedding: SheddingGame) -> None:
    hands = (MORE_ODD_CARDS, A_PAIR, ONE_CARD)
    position = a_table_of(shedding, hands, RUN_OUT, ON_TURN)

    assert shedding.legal_moves(position) == ()


def test_a_seat_with_nothing_to_do_is_passed_over_and_the_turn_goes_to_a_seat_that_has(
    shedding: SheddingGame,
) -> None:
    hands = (MORE_ODD_CARDS, A_PAIR, ONE_CARD)
    position = a_table_of(shedding, hands, RUN_OUT, ON_TURN)

    passed = fold(shedding.advance_round(position, None, Random(SEED)), position)

    assert passed.state.phase == SheddingPhase.SHEDDING
    assert passed.state.to_act == frozenset({FOLLOWING})
    assert passed.board == position.board


def test_a_seat_holding_no_set_while_the_stock_holds_a_card_is_left_its_draw(shedding: SheddingGame) -> None:
    hands = (MORE_ODD_CARDS, ODD_CARDS, ONE_CARD)
    position = a_table_of(shedding, hands, A_FEW, ON_TURN)

    assert shedding.advance_round(position, None, Random(SEED)) == ()
    assert shedding.legal_moves(position) == (a_draw(ON_TURN, A_FEW),)


def test_a_round_no_seat_may_act_in_is_decided_and_goes_to_the_shortest_hand(shedding: SheddingGame) -> None:
    hands = (MORE_ODD_CARDS, ONE_CARD, ODD_CARDS)
    position = a_table_of(shedding, hands, RUN_OUT, ON_TURN)

    decided = fold(shedding.advance_round(position, None, Random(SEED)), position)

    assert decided.state.phase == SheddingPhase.DECIDED
    assert decided.state.winner is None
    assert decided.state.to_act == frozenset()
    assert decided.state.round_points == (NOTHING, ROUND_POINT, NOTHING)
    assert shedding.round_over(decided)


def test_a_round_two_seats_stand_equally_short_in_goes_to_both_of_them(shedding: SheddingGame) -> None:
    hands = (ODD_CARDS, MORE_ODD_CARDS, (SIX_OF_DIAMONDS, EIGHT_OF_CLUBS))
    position = a_table_of(shedding, hands, RUN_OUT, ON_TURN)

    decided = fold(shedding.advance_round(position, None, Random(SEED)), position)

    assert decided.state.round_points == (ROUND_POINT, NOTHING, ROUND_POINT)


def test_shedding_from_a_group_this_game_holds_no_cards_in_is_refused(shedding: SheddingGame) -> None:
    seat = seat_on_turn(shedding)

    with pytest.raises(IllegalMove, match=f"sheds from its {HAND}"):
        shedding.submit(
            Move(player=seat, action=Discard(group="sleeve", indices=frozenset({0, 1}))),
            base_seq=shedding.head,
        )


def test_shedding_one_card_alone_is_refused(shedding: SheddingGame) -> None:
    seat = seat_on_turn(shedding)

    with pytest.raises(IllegalMove, match=f"sheds {SHED_LEAST} cards or more"):
        shedding.submit(a_shed(seat, frozenset({0})), base_seq=shedding.head)


def test_naming_a_position_the_hand_does_not_hold_is_refused(shedding: SheddingGame) -> None:
    seat = seat_on_turn(shedding)
    held = len(held_by(shedding, seat))

    with pytest.raises(IllegalMove, match=f"of a hand holding {held}"):
        shedding.submit(a_shed(seat, frozenset({0, held})), base_seq=shedding.head)


def test_shedding_cards_of_two_ranks_is_refused_and_leaves_the_table_as_it_stood(shedding: SheddingGame) -> None:
    hands = (ODD_CARDS + A_PAIR, MORE_ODD_CARDS, ONE_CARD)
    position = a_table_of(shedding, hands, left_over(hands), ON_TURN)
    standing, zones = shedding.state, every_zone(shedding)

    with pytest.raises(IllegalMove, match="reading as one rank, and named 2♠ 7♦"):
        shedding.validate(position, a_shed(ON_TURN, frozenset({0, 1})))

    assert shedding.state == standing
    assert every_zone(shedding) == zones


def test_drawing_from_a_zone_other_than_the_stock_is_refused(shedding: SheddingGame) -> None:
    seat = seat_on_turn(shedding)

    with pytest.raises(IllegalMove, match=f"draws from the {STOCK}"):
        shedding.submit(
            Move(player=seat, action=Take(group=DISCARD, indices=frozenset({0}))),
            base_seq=shedding.head,
        )


def test_drawing_from_a_stock_that_has_run_out_is_refused(shedding: SheddingGame) -> None:
    hands = (A_PAIR + ODD_CARDS, MORE_ODD_CARDS, ONE_CARD)
    position = a_table_of(shedding, hands, RUN_OUT, ON_TURN)

    with pytest.raises(IllegalMove, match=f"draws from a {STOCK} that has run out"):
        shedding.validate(position, Move(player=ON_TURN, action=Take(group=STOCK, indices=frozenset({0}))))


def test_drawing_a_card_other_than_the_one_at_the_end_of_the_stock_is_refused(shedding: SheddingGame) -> None:
    seat = seat_on_turn(shedding)

    with pytest.raises(IllegalMove, match=f"draws position \\[{stocked(shedding) - 1}\\] of the {STOCK}"):
        shedding.submit(
            Move(player=seat, action=Take(group=STOCK, indices=frozenset({0}))),
            base_seq=shedding.head,
        )


def test_an_intent_this_game_leaves_out_is_refused(shedding: SheddingGame) -> None:
    seat = seat_on_turn(shedding)

    with pytest.raises(IllegalMove, match="makes a discard or a take, and offered a play"):
        shedding.submit(
            Move(player=seat, action=Play(group=HAND, indices=frozenset({0}))),
            base_seq=shedding.head,
        )


def test_a_seat_the_turn_stands_away_from_is_refused(shedding: SheddingGame) -> None:
    waiting = next_seat(seat_on_turn(shedding), SEATS)
    hands = every_hand(shedding)

    with pytest.raises(NotYourTurn):
        shedding.submit(a_draw(waiting, stocked(shedding)), base_seq=shedding.head)

    assert every_hand(shedding) == hands


def test_every_move_listed_is_one_the_rules_carry_through(shedding: SheddingGame) -> None:
    hands = (A_TRIPLET + ONE_CARD, MORE_ODD_CARDS, ODD_CARDS)
    position = a_table_of(shedding, hands, A_FEW, ON_TURN)

    for move in shedding.legal_moves(position):
        shedding.step(position, move, Random(SEED))

    assert shedding.head == shedding.journal.head


def test_the_last_seat_of_the_table_hands_the_turn_back_to_the_first(shedding: SheddingGame) -> None:
    hands = (ODD_CARDS, MORE_ODD_CARDS, A_PAIR + ONE_CARD)
    position = a_table_of(shedding, hands, RUN_OUT, LAST_SEAT)

    laid = shedding.step(position, a_shed(LAST_SEAT, frozenset({0, 1})), Random(SEED))

    assert laid.state.to_act == frozenset({ON_TURN})
