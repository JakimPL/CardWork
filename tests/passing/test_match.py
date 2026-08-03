from dataclasses import dataclass
from random import Random
from typing import Final

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cardgames.passing.game import BEST, NEXT_BEST, PassingGame
from cardgames.passing.rules import NOTHING, WINNING_LEAD
from cardgames.passing.state import PassingPhase
from cardwork.decks.deck import Deck
from cardwork.effects.fold import fold
from cardwork.moves.actions import Give
from cardwork.moves.move import Move
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
    play_out,
    with_the_pile_run_out,
)

FULL_TABLE: Final[int] = 8
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


def test_the_pass_closing_a_turn_over_a_pile_run_out_draws_the_round_and_scores_nobody(
    passing: PassingGame,
) -> None:
    position = with_the_pile_run_out(passing)
    seat = position.state.current
    assert seat is not None

    drawn = passing.step(
        position,
        Move(player=seat, action=Give(target_player=next_seat(seat, SEATS), indices=frozenset({FIRST_CARD}))),
        Random(SEED),
    )

    assert drawn.state.phase == PassingPhase.DECIDED
    assert drawn.state.winner is None
    assert drawn.state.round_points == (NOTHING,) * SEATS
    assert drawn.state.to_act == frozenset()


def test_a_drawn_round_is_scored_into_the_standing_as_the_nothing_it_awarded(passing: PassingGame) -> None:
    position = with_the_pile_run_out(passing)
    seat = position.state.current
    assert seat is not None
    standing = position.state.points
    assert standing is not None

    drawn = passing.step(
        position,
        Move(player=seat, action=Give(target_player=next_seat(seat, SEATS), indices=frozenset({FIRST_CARD}))),
        Random(SEED),
    )
    closed = fold(passing.close_round(drawn), drawn)

    assert closed.state.points == standing
    assert closed.state.phase == MatchPhase.BETWEEN_ROUNDS
    assert closed.state.to_act == frozenset()


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
