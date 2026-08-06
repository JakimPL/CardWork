from random import Random
from typing import Final

from cardgames.backend.climbing.game import ClimbingGame
from cardgames.backend.climbing.state import ClimbingPhase
from cardwork.cards.cards import (
    ACE_OF_DIAMONDS,
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    KING_OF_CLUBS,
    NINE_OF_CLUBS,
    NINE_OF_SPADES,
    SEVEN_OF_DIAMONDS,
    THREE_OF_CLUBS,
    THREE_OF_HEARTS,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardsOrJokers
from cardwork.combinations.combination import Combination
from cardwork.states.state import NOTHING
from cardwork.zones.zone import cards_of
from cardwork.zones.zones import DISCARD, HANDS, STACK

from .driving import (
    NO_PASSES,
    SEED,
    a_combination_of,
    a_contest_of,
    a_lead_of,
    a_play,
    caught_with,
    passed_by,
)

LAID_IT: Final[int] = 0
FOLLOWING: Final[int] = 1
LAST_SEAT: Final[int] = 2
FOURTH_SEAT: Final[int] = 3
THE_PAIR: Final[frozenset[int]] = frozenset({0, 1})
NINES: Final[int] = 18
A_KING_AND_TWO_ODD_CARDS: Final[int] = 19

A_PAIR: Final[CardsOrJokers] = (FIVE_OF_SPADES, FIVE_OF_HEARTS)
A_LOWER_PAIR: Final[CardsOrJokers] = (THREE_OF_CLUBS, THREE_OF_HEARTS)
A_HIGHER_PAIR: Final[CardsOrJokers] = (NINE_OF_CLUBS, NINE_OF_SPADES)
ODD_CARDS: Final[CardsOrJokers] = (TWO_OF_SPADES, SEVEN_OF_DIAMONDS)
ONE_CARD: Final[CardsOrJokers] = (KING_OF_CLUBS,)
A_HIGH_CARD: Final[CardsOrJokers] = (ACE_OF_DIAMONDS,)

ANSWERING_HANDS: Final[tuple[CardsOrJokers, ...]] = (ONE_CARD, ODD_CARDS, A_HIGH_CARD, A_LOWER_PAIR)
GOING_OUT_HANDS: Final[tuple[CardsOrJokers, ...]] = (A_PAIR, A_HIGHER_PAIR, ONE_CARD + ODD_CARDS)
CLIMBING_OUT_HANDS: Final[tuple[CardsOrJokers, ...]] = (ONE_CARD, A_HIGHER_PAIR, ODD_CARDS)

PAIR_OF_FIVES: Final[Combination] = a_combination_of(A_PAIR)


def test_a_pass_hands_the_turn_to_the_next_seat_still_answering_and_moves_no_card(
    four_seats: ClimbingGame,
) -> None:
    position = a_contest_of(four_seats, ANSWERING_HANDS, FOLLOWING, PAIR_OF_FIVES, NO_PASSES)

    given_up = passed_by(four_seats, position, (FOLLOWING,))

    assert given_up.state.phase == ClimbingPhase.FOLLOW
    assert given_up.state.to_act == frozenset({LAST_SEAT})
    assert given_up.state.passed == frozenset({FOLLOWING})
    assert given_up.state.on_table == PAIR_OF_FIVES
    assert given_up.board == position.board


def test_a_contest_every_seat_but_one_has_passed_over_hands_that_seat_the_lead(four_seats: ClimbingGame) -> None:
    """The pass closing a contest leaves one seat in it, which is the seat whose combination the rest gave up on."""
    position = a_contest_of(four_seats, ANSWERING_HANDS, FOURTH_SEAT, PAIR_OF_FIVES, NO_PASSES)

    reopened = passed_by(four_seats, position, (FOURTH_SEAT, LAID_IT, FOLLOWING))

    assert reopened.state.phase == ClimbingPhase.LEAD
    assert reopened.state.to_act == frozenset({LAST_SEAT})
    assert reopened.state.on_table is None
    assert reopened.state.passed == NO_PASSES


def test_a_reopened_lead_stands_on_a_bare_table_with_the_combination_it_settled_out_of_play(
    four_seats: ClimbingGame,
) -> None:
    """The contest closing takes the combination that won it out of play, so the lead opens on nothing at all."""
    position = a_contest_of(four_seats, ANSWERING_HANDS, FOURTH_SEAT, PAIR_OF_FIVES, NO_PASSES)
    aside = cards_of(position.board.zone(DISCARD))

    reopened = passed_by(four_seats, position, (FOURTH_SEAT, LAID_IT, FOLLOWING))

    assert cards_of(reopened.board.zone(STACK)) == ()
    assert cards_of(reopened.board.zone(DISCARD)) == aside + PAIR_OF_FIVES.cards
    assert all(game_card.face_down for game_card in reopened.board.zone(DISCARD).cards)


def test_a_seat_that_has_given_its_turn_up_takes_a_turn_again_once_the_lead_reopens(four_seats: ClimbingGame) -> None:
    position = a_contest_of(four_seats, ANSWERING_HANDS, FOLLOWING, PAIR_OF_FIVES, NO_PASSES)

    given_up = passed_by(four_seats, position, (FOLLOWING,))
    reopened = passed_by(four_seats, given_up, (LAST_SEAT, FOURTH_SEAT))

    assert all(move.player != FOLLOWING for move in four_seats.legal_moves(given_up))
    assert reopened.state.to_act == frozenset({LAID_IT})
    assert four_seats.legal_moves(reopened) != ()
    assert all(move.player == LAID_IT for move in four_seats.legal_moves(reopened))


def test_at_two_seats_one_pass_settles_the_contest_for_the_seat_that_laid_the_combination(
    two_seats: ClimbingGame,
) -> None:
    position = a_contest_of(two_seats, (ONE_CARD, A_HIGHER_PAIR), FOLLOWING, PAIR_OF_FIVES, NO_PASSES)

    reopened = passed_by(two_seats, position, (FOLLOWING,))

    assert reopened.state.phase == ClimbingPhase.LEAD
    assert reopened.state.to_act == frozenset({LAID_IT})
    assert reopened.state.on_table is None


def test_a_seat_playing_its_last_card_closes_the_round_on_itself(climbing: ClimbingGame) -> None:
    position = a_lead_of(climbing, GOING_OUT_HANDS, LAID_IT)

    out = climbing.step(position, a_play(LAID_IT, THE_PAIR), Random(SEED))

    assert cards_of(out.board.zone(HANDS.of(LAID_IT))) == ()
    assert out.state.phase == ClimbingPhase.DECIDED
    assert out.state.winner == LAID_IT
    assert out.state.to_act == frozenset()
    assert out.state.passed == NO_PASSES
    assert climbing.round_over(out)


def test_a_round_decided_leaves_the_combination_that_won_it_lying_on_the_table(climbing: ClimbingGame) -> None:
    """The round closes on the play emptying a hand, so what took that seat out is what the table is left showing."""
    position = a_contest_of(climbing, CLIMBING_OUT_HANDS, FOLLOWING, PAIR_OF_FIVES, NO_PASSES)
    aside = cards_of(position.board.zone(DISCARD))

    out = climbing.step(position, a_play(FOLLOWING, THE_PAIR), Random(SEED))

    assert out.state.phase == ClimbingPhase.DECIDED
    assert out.state.winner == FOLLOWING
    assert cards_of(out.board.zone(STACK)) == A_HIGHER_PAIR
    assert cards_of(out.board.zone(DISCARD)) == aside + PAIR_OF_FIVES.cards


def test_the_round_catches_every_seat_with_the_worth_of_the_cards_left_in_its_hand(climbing: ClimbingGame) -> None:
    """Pips count for themselves and every court card and ace for ten, so a king and a two and a seven are 19."""
    position = a_lead_of(climbing, GOING_OUT_HANDS, LAID_IT)

    out = climbing.step(position, a_play(LAID_IT, THE_PAIR), Random(SEED))

    assert out.state.round_points == (NOTHING, NINES, A_KING_AND_TWO_ODD_CARDS)
    assert out.state.round_points == tuple(caught_with(hand) for hand in out.held(HANDS))
    assert out.state.points == (NOTHING,) * climbing.players


def test_the_seat_that_went_out_is_caught_with_nothing(climbing: ClimbingGame) -> None:
    position = a_lead_of(climbing, GOING_OUT_HANDS, LAID_IT)

    out = climbing.step(position, a_play(LAID_IT, THE_PAIR), Random(SEED))

    assert out.state.round_points[LAID_IT] == NOTHING
    assert caught_with(out.board.cards(HANDS.of(LAID_IT))) == NOTHING


def test_a_round_standing_decided_is_left_as_it_stands(climbing: ClimbingGame) -> None:
    """A round comes to rest at the boundary that scores it, so the close it has been written is owed once."""
    position = a_lead_of(climbing, GOING_OUT_HANDS, LAID_IT)
    out = climbing.step(position, a_play(LAID_IT, THE_PAIR), Random(SEED))

    assert climbing.advance_round(out, None, Random(SEED)) == ()
