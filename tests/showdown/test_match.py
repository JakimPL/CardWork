from dataclasses import dataclass
from random import Random
from typing import Final

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cardgames.backend.showdown.game import ShowdownGame
from cardgames.backend.showdown.rules import (
    BLIND_SIZE,
    FIRST_TURN,
    HAND_SIZE,
    NOTHING,
    ONE_TURN,
    TURNS,
)
from cardgames.backend.showdown.state import ShowdownPhase
from cardgames.backend.showdown.zones import DISCARD, STOCK, blind_of, hand_of
from cardwork.rounds.conclusion import ONE_ROUND
from cardwork.rounds.seating import next_seat
from cardwork.rounds.state import MatchPhase
from tests.cases import Case, descriptions

from .driving import (
    FULL_TABLE,
    ROUNDS,
    SEATS,
    SEED,
    TWO_SEATS,
    a_match,
    commit_whatever_is_held,
    play_a_round,
    play_out,
)

SECOND_ROUND: Final[int] = 2
SECOND_TURN: Final[int] = 2
STOCKED_AFRESH: Final[int] = 22
REVEAL_AND_BOUNDARY: Final[int] = 3
SEEDS: Final[range] = range(10)


@dataclass(frozen=True)
class MatchCase(Case):
    players: int
    rounds: int
    seed: int


MATCHES: Final[tuple[MatchCase, ...]] = (
    MatchCase(description="two seats over one round", players=TWO_SEATS, rounds=ONE_ROUND, seed=SEED),
    MatchCase(description="three seats over two rounds", players=SEATS, rounds=ROUNDS, seed=SEED),
    MatchCase(description="five seats over two rounds", players=FULL_TABLE, rounds=ROUNDS, seed=SEED),
)


def a_match_played_out(case: MatchCase) -> ShowdownGame:
    """The table of that case driven to rest, its moves chosen by a generator of the case's own seed."""
    game = a_match(case.players, case.rounds, case.seed)
    play_out(game, Random(case.seed).choice)
    return game


def test_each_turn_of_a_round_reveals_one_card_of_every_seat(showdown: ShowdownGame) -> None:
    turned_over = []
    reached = []
    for _ in range(TURNS):
        commit_whatever_is_held(showdown)
        turned_over.append(len(showdown.board.zone(DISCARD).cards))
        reached.append(showdown.state.turn_number)

    assert turned_over == [SEATS * turn for turn in range(ONE_TURN, TURNS)] + [NOTHING]
    assert reached == list(range(SECOND_TURN, TURNS + ONE_TURN)) + [FIRST_TURN]


def test_ten_turns_run_both_holdings_out_and_the_round_that_follows_is_dealt_afresh(showdown: ShowdownGame) -> None:
    play_a_round(showdown)

    assert all(len(showdown.board.zone(hand_of(seat)).cards) == HAND_SIZE for seat in range(SEATS))
    assert all(len(showdown.board.zone(blind_of(seat)).cards) == BLIND_SIZE for seat in range(SEATS))
    assert len(showdown.board.zone(DISCARD).cards) == NOTHING
    assert len(showdown.board.zone(STOCK).cards) == STOCKED_AFRESH
    assert showdown.state.round_number == SECOND_ROUND
    assert showdown.state.turn_number == FIRST_TURN
    assert showdown.state.phase == ShowdownPhase.COMMITTING


def test_what_a_round_scored_is_what_the_standing_is_given_and_the_next_round_starts_from_zero(
    showdown: ShowdownGame,
) -> None:
    leader = showdown.state.led_by

    revealed, closed, opened = play_a_round(showdown)

    assert closed.effects[-1].state.points == revealed.effects[-1].state.round_points
    assert showdown.state.points == closed.effects[-1].state.points
    assert sum(showdown.state.points) > NOTHING
    assert showdown.state.round_points == (NOTHING,) * SEATS
    assert showdown.state.led_by == next_seat(leader, SEATS)
    assert (revealed.move, closed.move, opened.move) == (None, None, None)


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_a_match_closes_once_it_has_played_the_rounds_it_was_built_for(case: MatchCase) -> None:
    game = a_match_played_out(case)

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert game.state.round_number == case.rounds
    assert sum(game.state.points) > NOTHING
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


def test_a_match_of_one_round_closes_on_that_round_and_leaves_its_cards_where_they_lie(
    two_seats: ShowdownGame,
) -> None:
    settled = play_a_round(two_seats)

    assert len(settled) == REVEAL_AND_BOUNDARY
    assert two_seats.state.phase == MatchPhase.MATCH_OVER
    assert two_seats.state.round_number == ONE_ROUND
    assert two_seats.state.points == settled[0].effects[-1].state.round_points
    assert len(two_seats.board.zone(DISCARD).cards) == TURNS * TWO_SEATS


@given(seed=st.sampled_from(SEEDS))
@settings(deadline=None, max_examples=len(SEEDS))
def test_a_match_dealt_and_played_from_any_generator_runs_its_rounds_out(seed: int) -> None:
    game = a_match(SEATS, ROUNDS, seed)

    play_out(game, Random(seed).choice)

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert game.state.round_number == ROUNDS
    assert game.snapshot(game.head) == game.replay()
    for seq in range(game.head + 1):
        game.snapshot(seq).board.validate_board()
