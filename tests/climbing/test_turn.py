from random import Random
from typing import Final

import pytest

from cardgames.backend.climbing.game import ClimbingGame
from cardgames.backend.climbing.state import ClimbingPhase, ClimbingState
from cardwork.cards.cards import (
    ACE_OF_DIAMONDS,
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    FOUR_OF_SPADES,
    KING_OF_CLUBS,
    NINE_OF_CLUBS,
    NINE_OF_SPADES,
    SEVEN_OF_DIAMONDS,
    SEVEN_OF_SPADES,
    SIX_OF_SPADES,
    THREE_OF_CLUBS,
    THREE_OF_HEARTS,
    THREE_OF_SPADES,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardsOrJokers
from cardwork.combinations.combination import Combination
from cardwork.exceptions import IllegalMove, NotYourTurn
from cardwork.moves.actions import Discard, Play
from cardwork.moves.move import Move
from cardwork.rounds.seating import next_seat
from cardwork.zones.zone import cards_of
from cardwork.zones.zones import HANDS, STACK

from .driving import (
    NO_PASSES,
    SEATS,
    SEED,
    a_combination_of,
    a_contest_of,
    a_lead_of,
    a_pass,
    a_play,
    every_hand,
    every_zone,
    give_the_turn_up,
    held_by,
    seat_on_turn,
    turn_of,
)

ON_TURN: Final[int] = 0
FOLLOWING: Final[int] = 1
LAST_SEAT: Final[int] = 2
FOURTH_SEAT: Final[int] = 3
THE_FIRST_PAIR: Final[frozenset[int]] = frozenset({0, 1})
THE_SECOND_PAIR: Final[frozenset[int]] = frozenset({2, 3})
A_SINGLE: Final[frozenset[int]] = frozenset({0})

A_PAIR: Final[CardsOrJokers] = (FIVE_OF_SPADES, FIVE_OF_HEARTS)
A_LOWER_PAIR: Final[CardsOrJokers] = (THREE_OF_CLUBS, THREE_OF_HEARTS)
A_HIGHER_PAIR: Final[CardsOrJokers] = (NINE_OF_CLUBS, NINE_OF_SPADES)
ODD_CARDS: Final[CardsOrJokers] = (TWO_OF_SPADES, SEVEN_OF_DIAMONDS)
ONE_CARD: Final[CardsOrJokers] = (KING_OF_CLUBS,)
A_HIGH_CARD: Final[CardsOrJokers] = (ACE_OF_DIAMONDS,)
ODD_HANDS: Final[tuple[CardsOrJokers, ...]] = (A_PAIR + ODD_CARDS, A_HIGHER_PAIR, ONE_CARD)
ANSWERING_HANDS: Final[tuple[CardsOrJokers, ...]] = (
    ONE_CARD,
    ODD_CARDS,
    A_HIGHER_PAIR + A_HIGH_CARD,
    A_LOWER_PAIR,
)
CLIMBING_HANDS: Final[tuple[CardsOrJokers, ...]] = (
    (TWO_OF_SPADES, FIVE_OF_SPADES),
    (THREE_OF_SPADES, SIX_OF_SPADES),
    (FOUR_OF_SPADES, SEVEN_OF_SPADES),
)

PAIR_OF_FIVES: Final[Combination] = a_combination_of(A_PAIR)
PAIR_OF_NINES: Final[Combination] = a_combination_of(A_HIGHER_PAIR)
THE_KING: Final[Combination] = a_combination_of(ONE_CARD)


def test_a_play_lays_the_combination_face_up_on_the_stack_and_hands_the_turn_on(climbing: ClimbingGame) -> None:
    position = a_lead_of(climbing, ODD_HANDS, ON_TURN)

    laid = climbing.step(position, a_play(ON_TURN, THE_FIRST_PAIR), Random(SEED))

    assert cards_of(laid.board.zone(STACK)) == A_PAIR
    assert all(not game_card.face_down for game_card in laid.board.zone(STACK).cards)
    assert cards_of(laid.board.zone(HANDS.of(ON_TURN))) == ODD_CARDS
    assert laid.state.phase == ClimbingPhase.FOLLOW
    assert laid.state.to_act == frozenset({FOLLOWING})
    laid.board.validate_board()


def test_the_cursor_a_landed_combination_leaves_carries_it_as_the_ranking_read_it(climbing: ClimbingGame) -> None:
    """A seat answering is held to the combination itself, so the cursor states the reading rather than a count."""
    position = a_lead_of(climbing, ODD_HANDS, ON_TURN)

    laid = climbing.step(position, a_play(ON_TURN, THE_FIRST_PAIR), Random(SEED))

    assert laid.state.on_table == PAIR_OF_FIVES
    assert laid.state.passed == NO_PASSES


def test_the_cursor_a_landed_combination_leaves_crosses_the_wire_as_it_stands(climbing: ClimbingGame) -> None:
    """The combination is carried whole, so a client and a replay each read the contest a seat is answering."""
    position = a_lead_of(climbing, ODD_HANDS, ON_TURN)
    laid = climbing.step(position, a_play(ON_TURN, THE_FIRST_PAIR), Random(SEED))

    restored = ClimbingState.model_validate_json(laid.state.model_dump_json())

    assert restored == laid.state
    assert restored.on_table == PAIR_OF_FIVES


def test_a_climb_lands_on_the_stack_and_leaves_the_seats_that_gave_their_turn_up_out_of_the_contest(
    four_seats: ClimbingGame,
) -> None:
    position = a_contest_of(four_seats, ANSWERING_HANDS, LAST_SEAT, PAIR_OF_FIVES, frozenset({FOLLOWING}))

    climbed = four_seats.step(position, a_play(LAST_SEAT, THE_FIRST_PAIR), Random(SEED))

    assert cards_of(climbed.board.zone(STACK)) == PAIR_OF_FIVES.cards + A_HIGHER_PAIR
    assert climbed.state.on_table == PAIR_OF_NINES
    assert climbed.state.passed == frozenset({FOLLOWING})
    assert climbed.state.to_act == frozenset({FOURTH_SEAT})
    climbed.board.validate_board()


def test_the_turn_of_a_contest_walks_past_the_seats_that_have_passed(four_seats: ClimbingGame) -> None:
    """A pass takes a seat out of the contest, so the turn reaches the seats still answering and no others."""
    position = a_contest_of(four_seats, ANSWERING_HANDS, LAST_SEAT, PAIR_OF_FIVES, frozenset({FOURTH_SEAT}))

    climbed = four_seats.step(position, a_play(LAST_SEAT, THE_FIRST_PAIR), Random(SEED))

    assert climbed.state.to_act == frozenset({ON_TURN})


def test_the_turn_travels_round_the_table_from_the_seat_leading_the_round(climbing: ClimbingGame) -> None:
    """Each seat climbs over the single before it, so the turn passes on round the table and back again."""
    position = a_lead_of(climbing, CLIMBING_HANDS, ON_TURN)

    turns = [turn_of(position)]
    for _ in range(SEATS):
        position = climbing.step(position, a_play(turn_of(position), A_SINGLE), Random(SEED))
        turns.append(turn_of(position))

    assert turns == [place % SEATS for place in range(SEATS + 1)]


def test_a_seat_answering_a_combination_is_offered_the_ones_that_climb_over_it_and_the_pass_beside_them(
    climbing: ClimbingGame,
) -> None:
    hands = (ONE_CARD, A_LOWER_PAIR + A_HIGHER_PAIR, ODD_CARDS)
    position = a_contest_of(climbing, hands, FOLLOWING, PAIR_OF_FIVES, NO_PASSES)

    moves = climbing.legal_moves(position)

    assert all(move.player == FOLLOWING for move in moves)
    assert tuple(move.action.indices for move in moves if isinstance(move.action, Play)) == (THE_SECOND_PAIR,)
    assert moves[-1] == a_pass(FOLLOWING)


def test_a_seat_holding_no_combination_of_the_count_on_the_table_is_offered_the_pass_alone(
    climbing: ClimbingGame,
) -> None:
    hands = (ONE_CARD, ODD_CARDS, A_HIGHER_PAIR)
    position = a_contest_of(climbing, hands, FOLLOWING, PAIR_OF_FIVES, NO_PASSES)

    assert climbing.legal_moves(position) == (a_pass(FOLLOWING),)


def test_a_round_standing_decided_offers_no_move_at_all(climbing: ClimbingGame) -> None:
    position = a_lead_of(climbing, ODD_HANDS, ON_TURN)
    decided = position.with_state(position.state.at_rest(ClimbingPhase.DECIDED, winner=ON_TURN))

    assert climbing.legal_moves(decided) == ()
    assert climbing.round_over(decided)


def test_every_move_listed_is_one_the_rules_carry_through(climbing: ClimbingGame) -> None:
    position = a_lead_of(climbing, ODD_HANDS, ON_TURN)

    for move in climbing.legal_moves(position):
        climbing.step(position, move, Random(SEED))

    assert climbing.head == climbing.journal.head


def test_playing_out_of_a_group_this_game_holds_no_cards_in_is_refused(climbing: ClimbingGame) -> None:
    seat = seat_on_turn(climbing)

    with pytest.raises(IllegalMove, match=f"plays out of its {HANDS.name}"):
        climbing.submit(
            Move(player=seat, action=Play(group="sleeve", indices=A_SINGLE)),
            base_seq=climbing.head,
        )


def test_naming_a_position_the_hand_does_not_hold_is_refused(climbing: ClimbingGame) -> None:
    seat = seat_on_turn(climbing)
    held = len(held_by(climbing, seat))

    with pytest.raises(IllegalMove, match=f"named position {held} of a hand holding {held}"):
        climbing.submit(a_play(seat, frozenset({held})), base_seq=climbing.head)


def test_playing_cards_reading_as_no_combination_is_refused_and_leaves_the_table_as_it_stood(
    climbing: ClimbingGame,
) -> None:
    position = a_lead_of(climbing, ODD_HANDS, ON_TURN)
    standing, zones = climbing.state, every_zone(climbing)

    with pytest.raises(IllegalMove, match="plays a combination this game is played by, and named 2♠ 7♦"):
        climbing.validate(position, a_play(ON_TURN, THE_SECOND_PAIR))

    assert climbing.state == standing
    assert every_zone(climbing) == zones


def test_a_combination_standing_no_higher_than_the_one_on_the_table_is_refused(climbing: ClimbingGame) -> None:
    hands = (ONE_CARD, A_PAIR, ODD_CARDS)
    position = a_contest_of(climbing, hands, FOLLOWING, PAIR_OF_NINES, NO_PASSES)

    with pytest.raises(IllegalMove, match=f"climbs over {PAIR_OF_NINES}, and played {PAIR_OF_FIVES}"):
        climbing.validate(position, a_play(FOLLOWING, THE_FIRST_PAIR))


def test_a_combination_of_another_count_than_the_one_on_the_table_is_refused(climbing: ClimbingGame) -> None:
    """A contest is settled within a count, so a single stands beside a pair rather than over it."""
    hands = (A_HIGHER_PAIR, ONE_CARD, ODD_CARDS)
    position = a_contest_of(climbing, hands, FOLLOWING, PAIR_OF_FIVES, NO_PASSES)

    with pytest.raises(IllegalMove, match=f"climbs over {PAIR_OF_FIVES}, and played {THE_KING}"):
        climbing.validate(position, a_play(FOLLOWING, A_SINGLE))


def test_playing_into_a_round_that_stands_decided_is_refused(climbing: ClimbingGame) -> None:
    position = a_lead_of(climbing, ODD_HANDS, ON_TURN)
    decided = position.with_state(position.state.at_rest(ClimbingPhase.DECIDED, winner=LAST_SEAT))

    with pytest.raises(
        IllegalMove,
        match=f"plays on lead or in answer, and the round stands in the {ClimbingPhase.DECIDED} phase",
    ):
        climbing.validate(decided, a_play(ON_TURN, THE_FIRST_PAIR))


def test_passing_over_a_table_standing_on_nothing_is_refused(climbing: ClimbingGame) -> None:
    with pytest.raises(IllegalMove, match="passes over a combination on the table"):
        give_the_turn_up(climbing)


def test_passing_twice_over_one_combination_is_refused(climbing: ClimbingGame) -> None:
    hands = (ONE_CARD, ODD_CARDS, A_HIGHER_PAIR)
    position = a_contest_of(climbing, hands, FOLLOWING, PAIR_OF_FIVES, frozenset({FOLLOWING}))

    with pytest.raises(IllegalMove, match="passes once over a combination, and has passed over this one"):
        climbing.validate(position, a_pass(FOLLOWING))


def test_an_intent_this_game_leaves_out_is_refused(climbing: ClimbingGame) -> None:
    seat = seat_on_turn(climbing)

    with pytest.raises(IllegalMove, match="makes a pass or a play, and offered a discard"):
        climbing.submit(
            Move(player=seat, action=Discard(group=HANDS.name, indices=A_SINGLE)),
            base_seq=climbing.head,
        )


def test_a_seat_the_turn_stands_away_from_is_refused(climbing: ClimbingGame) -> None:
    waiting = next_seat(seat_on_turn(climbing), SEATS)
    hands = every_hand(climbing)

    with pytest.raises(NotYourTurn):
        climbing.submit(a_play(waiting, A_SINGLE), base_seq=climbing.head)

    assert every_hand(climbing) == hands
