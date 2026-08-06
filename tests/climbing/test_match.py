from dataclasses import dataclass
from random import Random
from typing import Final

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cardgames.backend.climbing.game import ClimbingGame
from cardgames.backend.climbing.state import ClimbingPhase
from cardwork.cards.cards import (
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    KING_OF_CLUBS,
    NINE_OF_CLUBS,
    NINE_OF_SPADES,
    SEVEN_OF_DIAMONDS,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardsOrJokers
from cardwork.effects.fold import fold
from cardwork.rounds.conclusion import ONE_ROUND
from cardwork.rounds.state import MatchPhase
from cardwork.states.award import Award
from cardwork.states.state import NOTHING, Points
from cardwork.zones.zones import DISCARD, HANDS, STACK
from tests.cases import Case, descriptions

from .driving import (
    FOUR_SEATS,
    FULL_TABLE,
    ROUNDS,
    SEATS,
    SEED,
    a_lead_of,
    a_match,
    a_play,
    caught_with,
    climbing_first,
    passing_first,
    play_a_round,
    play_out,
)

LAID_IT: Final[int] = 0
THE_PAIR: Final[frozenset[int]] = frozenset({0, 1})
SEEDS: Final[range] = range(8)
NO_CARDS: Final[int] = 0
CARDS_LEFT_OVER: Final[int] = 1

A_PAIR: Final[CardsOrJokers] = (FIVE_OF_SPADES, FIVE_OF_HEARTS)
A_HIGHER_PAIR: Final[CardsOrJokers] = (NINE_OF_CLUBS, NINE_OF_SPADES)
ODD_CARDS: Final[CardsOrJokers] = (TWO_OF_SPADES, SEVEN_OF_DIAMONDS)
ONE_CARD: Final[CardsOrJokers] = (KING_OF_CLUBS,)
GOING_OUT_HANDS: Final[tuple[CardsOrJokers, ...]] = (A_PAIR, A_HIGHER_PAIR, ONE_CARD + ODD_CARDS)


@dataclass(frozen=True)
class MatchCase(Case):
    players: int
    rounds: int
    seed: int


MATCHES: Final[tuple[MatchCase, ...]] = (
    MatchCase(description="three seats over one round", players=SEATS, rounds=ONE_ROUND, seed=SEED),
    MatchCase(description="four seats over two rounds", players=FOUR_SEATS, rounds=ROUNDS, seed=SEED),
    MatchCase(description="a full table over two rounds", players=FULL_TABLE, rounds=ROUNDS, seed=SEED),
)


def a_match_played_out(case: MatchCase) -> ClimbingGame:
    """The table of that case driven to rest, its moves chosen by a generator of the case's own seed."""
    game = a_match(case.players, case.rounds, case.seed)
    play_out(game, Random(case.seed).choice)
    return game


def every_round_scored(game: ClimbingGame) -> tuple[Points, ...]:
    """What each round of a played-out match scored, read off the cursors those rounds came to rest on.

    A round is scored at the one cursor that decides it, so this reads the rounds out of the record rather than
    off the play, which is how the standing of record is held to what the rounds it adds up came to.
    """
    return tuple(
        game.snapshot(seq).state.round_points
        for seq in range(game.head + 1)
        if game.snapshot(seq).state.phase == ClimbingPhase.DECIDED
    )


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_a_match_comes_to_rest_once_it_has_played_the_rounds_it_was_built_for(case: MatchCase) -> None:
    game = a_match_played_out(case)

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert game.state.round_number == case.rounds
    assert game.state.to_act == frozenset()
    assert game.legal_moves(game.position) == ()
    assert game.settle() == ()


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_the_standing_of_a_match_is_what_its_rounds_caught_each_seat_with(case: MatchCase) -> None:
    game = a_match_played_out(case)
    scored = every_round_scored(game)

    assert len(scored) == case.rounds
    assert game.state.points == tuple(sum(award) for award in zip(*scored, strict=True))


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_every_round_of_a_match_takes_one_seat_out_and_catches_the_rest_with_what_they_hold(
    case: MatchCase,
) -> None:
    """A round closes on a hand played out, so one seat is caught with nothing and every other with something."""
    game = a_match_played_out(case)

    for award in every_round_scored(game):
        assert min(award) == NOTHING
        assert sum(award) > NOTHING


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_a_match_of_climbing_is_played_towards_the_low_end_of_the_standing(case: MatchCase) -> None:
    """A standing counted in penalties is won by the seat caught with the least, which the cursor states."""
    game = a_match_played_out(case)

    assert game.state.award == Award.LOWEST


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_a_match_runs_its_rounds_out_to_the_cards_it_was_dealt_from(case: MatchCase) -> None:
    game = a_match_played_out(case)
    played = game.board.count(STACK)
    aside = game.board.count(DISCARD)
    held = sum(len(game.board.cards(HANDS.of(seat))) for seat in range(case.players))

    assert played + aside + held == len(game.board.starting_deck)
    for seq in range(game.head + 1):
        game.snapshot(seq).board.validate_board()


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_the_memo_matches_a_replay_at_every_sequence_a_match_passes_through(case: MatchCase) -> None:
    game = a_match_played_out(case)

    assert all(game.snapshot(seq) == game.replay(seq) for seq in range(game.head + 1))


def test_a_match_whose_seats_give_their_turn_up_wherever_they_may_still_plays_its_rounds_out(
    four_seats: ClimbingGame,
) -> None:
    """A table that passes at every chance runs its rounds through their reopened leads and out to the close."""
    play_out(four_seats, passing_first)

    assert four_seats.state.phase == MatchPhase.MATCH_OVER
    assert four_seats.state.round_number == ROUNDS
    assert four_seats.state.points == tuple(sum(award) for award in zip(*every_round_scored(four_seats), strict=True))


def test_a_match_of_two_seats_plays_its_round_out_to_a_standing_of_what_each_was_caught_with(
    two_seats: ClimbingGame,
) -> None:
    """One pass settles a contest at two seats, so a round there is a run of leads and one answer to each."""
    play_out(two_seats, Random(SEED).choice)

    assert two_seats.state.phase == MatchPhase.MATCH_OVER
    assert two_seats.state.points == tuple(sum(award) for award in zip(*every_round_scored(two_seats), strict=True))
    assert two_seats.state.round_number == ONE_ROUND


def test_a_decided_round_is_scored_into_the_standing_and_the_table_left_between_rounds(
    climbing: ClimbingGame,
) -> None:
    position = a_lead_of(climbing, GOING_OUT_HANDS, LAID_IT)

    out = climbing.step(position, a_play(LAID_IT, THE_PAIR), Random(SEED))
    closed = fold(climbing.close_round(out), out)

    assert out.state.phase == ClimbingPhase.DECIDED
    assert closed.state.points == out.state.round_points
    assert closed.state.phase == MatchPhase.BETWEEN_ROUNDS
    assert closed.state.to_act == frozenset()


def test_the_round_after_one_decided_opens_on_the_seat_that_went_out_of_it(climbing: ClimbingGame) -> None:
    play_a_round(climbing, climbing_first)
    caught = climbing.state.round_points
    gone_out = climbing.state.winner
    climbing.settle()

    assert climbing.state.phase == ClimbingPhase.LEAD
    assert climbing.state.led_by == gone_out
    assert climbing.state.round_number == ROUNDS
    assert climbing.state.points == caught
    assert climbing.state.round_points == (NOTHING,) * SEATS
    assert climbing.state.on_table is None
    assert climbing.state.passed == frozenset()
    assert climbing.state.winner is None


def test_the_deal_of_the_next_round_gathers_the_cards_a_round_spent_back_into_the_pile(
    climbing: ClimbingGame,
) -> None:
    """Every combination beaten goes out of play as a round runs, and the deal that follows takes them all back."""
    play_a_round(climbing, climbing_first)
    spent = climbing.board.count(DISCARD)
    climbing.settle()

    assert spent > CARDS_LEFT_OVER
    assert climbing.board.count(DISCARD) == CARDS_LEFT_OVER
    assert climbing.board.count(STACK) == NO_CARDS
    climbing.board.validate_board()


def test_a_round_leaves_every_seat_holding_cards_caught_with_what_they_are_worth(climbing: ClimbingGame) -> None:
    play_a_round(climbing, climbing_first)

    assert climbing.state.round_points == tuple(caught_with(hand) for hand in climbing.position.held(HANDS))


@given(seed=st.sampled_from(SEEDS))
@settings(deadline=None, max_examples=len(SEEDS))
def test_a_match_dealt_and_played_from_any_generator_runs_its_rounds_out(seed: int) -> None:
    game = a_match(SEATS, ROUNDS, seed)

    play_out(game, Random(seed).choice)

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert game.state.round_number == ROUNDS
    assert game.state.points == tuple(sum(award) for award in zip(*every_round_scored(game), strict=True))
    assert game.snapshot(game.head) == game.replay()
    for seq in range(game.head + 1):
        game.snapshot(seq).board.validate_board()
