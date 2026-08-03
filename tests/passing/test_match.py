from dataclasses import dataclass
from random import Random
from typing import Final

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cardgames.passing.game import BEST, NEXT_BEST, PassingGame
from cardgames.passing.rules import NOTHING, WINNING_LEAD
from cardgames.passing.state import PassingPhase
from cardgames.passing.zones import PILE
from cardwork.decks.deck import Deck
from cardwork.rounds.seating import next_seat
from cardwork.rounds.state import MatchPhase

from ..cases import Case, descriptions
from .driving import (
    FIRST_CARD,
    JOKERED_DECK,
    PLAIN_DECK,
    SEATS,
    SEED,
    TWO_SEATS,
    a_match,
    exchange_until_the_pile_runs_out,
    pass_on,
    play_out,
)

FULL_TABLE: Final[int] = 8
SECOND_ROUND: Final[int] = 2
BOUNDARY_TRANSACTIONS: Final[int] = 2
PILED_AFRESH: Final[int] = 45
SEEDS: Final[range] = range(10)


@dataclass(frozen=True)
class MatchCase(Case):
    players: int
    deck: Deck
    seed: int


MATCHES: Final[tuple[MatchCase, ...]] = (
    MatchCase(
        description="two seats over one deck",
        players=TWO_SEATS,
        deck=PLAIN_DECK,
        seed=SEED,
    ),
    MatchCase(
        description="three seats over one deck and two jokers",
        players=SEATS,
        deck=JOKERED_DECK,
        seed=SEED,
    ),
)


def a_match_played_out(case: MatchCase) -> PassingGame:
    """The table of that case driven to rest, its moves chosen by a generator of the case's own seed."""
    game = a_match(case.players, case.deck, case.seed)
    play_out(game, Random(case.seed).choice)
    return game


def test_the_pile_running_out_draws_the_round_and_scores_nobody(two_seats: PassingGame) -> None:
    exchange_until_the_pile_runs_out(two_seats)

    pass_on(two_seats, FIRST_CARD)

    assert two_seats.state.phase == PassingPhase.DECIDED
    assert two_seats.state.winner is None
    assert two_seats.state.round_points == (NOTHING,) * TWO_SEATS
    assert two_seats.state.to_act == frozenset()


def test_a_drawn_round_is_followed_by_a_fresh_deal_on_the_standing_it_left(two_seats: PassingGame) -> None:
    exchange_until_the_pile_runs_out(two_seats)
    leader = two_seats.state.led_by

    pass_on(two_seats, FIRST_CARD)
    settled = two_seats.settle()

    assert two_seats.state.points == (NOTHING,) * TWO_SEATS
    assert two_seats.state.round_number == SECOND_ROUND
    assert two_seats.state.phase == PassingPhase.PASSING
    assert two_seats.state.led_by == next_seat(leader, TWO_SEATS)
    assert len(two_seats.board.zone(PILE).cards) == PILED_AFRESH
    assert len(settled) == BOUNDARY_TRANSACTIONS
    assert all(transaction.move is None for transaction in settled)


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_a_match_closes_once_one_seat_leads_the_next_best_by_two(case: MatchCase) -> None:
    game = a_match_played_out(case)
    standing = sorted(game.state.points, reverse=True)

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert standing[BEST] - standing[NEXT_BEST] >= WINNING_LEAD
    assert sum(game.state.points) <= game.state.round_number
    assert game.state.to_act == frozenset()
    assert game.legal_moves(game.position) == ()
    assert game.settle() == ()


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_the_memo_matches_a_replay_at_every_sequence_a_match_passes_through(case: MatchCase) -> None:
    game = a_match_played_out(case)

    assert all(game.snapshot(seq) == game.replay(seq) for seq in range(game.head + 1))


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_every_position_a_match_reached_holds_the_deck_it_started_from(case: MatchCase) -> None:
    game = a_match_played_out(case)

    for seq in range(game.head + 1):
        game.snapshot(seq).board.validate_board()


def test_a_full_table_plays_a_match_out_to_the_deck_it_started_from() -> None:
    game = a_match(FULL_TABLE, PLAIN_DECK, SEED)

    play_out(game, Random(SEED).choice)

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert game.snapshot(game.head) == game.replay()
    for seq in range(game.head + 1):
        game.snapshot(seq).board.validate_board()


@given(seed=st.sampled_from(SEEDS))
@settings(deadline=None, max_examples=len(SEEDS))
def test_a_match_dealt_and_played_from_any_generator_closes_on_a_lead_of_two(seed: int) -> None:
    game = a_match(SEATS, JOKERED_DECK, seed)

    play_out(game, Random(seed).choice)
    standing = sorted(game.state.points, reverse=True)

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert standing[BEST] - standing[NEXT_BEST] >= WINNING_LEAD
    assert game.snapshot(game.head) == game.replay()
    for seq in range(game.head + 1):
        game.snapshot(seq).board.validate_board()
