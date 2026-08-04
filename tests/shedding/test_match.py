from dataclasses import dataclass
from random import Random
from typing import Final

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cardgames.backend.shedding.game import SheddingGame
from cardgames.backend.shedding.rules import NOTHING, ROUND_POINT
from cardgames.backend.shedding.state import SheddingPhase
from cardgames.backend.shedding.zones import STOCK
from cardwork.cards.cards import (
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    KING_OF_CLUBS,
    NINE_OF_DIAMONDS,
)
from cardwork.cards.game import CardsOrJokers
from cardwork.effects.fold import fold
from cardwork.rounds.conclusion import ONE_ROUND
from cardwork.rounds.state import MatchPhase
from cardwork.zones.zone import hand_of
from cardwork.zones.zones import DISCARD
from tests.cases import Case, descriptions

from .driving import (
    FULL_TABLE,
    ROUNDS,
    SEATS,
    SEED,
    TWO_SEATS,
    a_match,
    a_shed,
    a_table_of,
    left_over,
    play_out,
)

ON_TURN: Final[int] = 0
RUN_OUT: Final[int] = 0
SEEDS: Final[range] = range(8)
A_PAIR: Final[CardsOrJokers] = (FIVE_OF_SPADES, FIVE_OF_HEARTS)
ONE_CARD: Final[CardsOrJokers] = (KING_OF_CLUBS,)
ANOTHER_CARD: Final[CardsOrJokers] = (NINE_OF_DIAMONDS,)


@dataclass(frozen=True)
class MatchCase(Case):
    players: int
    rounds: int
    seed: int


MATCHES: Final[tuple[MatchCase, ...]] = (
    MatchCase(description="two seats over one round", players=TWO_SEATS, rounds=ONE_ROUND, seed=SEED),
    MatchCase(description="three seats over two rounds", players=SEATS, rounds=ROUNDS, seed=SEED),
    MatchCase(description="a full table over two rounds", players=FULL_TABLE, rounds=ROUNDS, seed=SEED),
)


def a_match_played_out(case: MatchCase) -> SheddingGame:
    """The table of that case driven to rest, its moves chosen by a generator of the case's own seed."""
    game = a_match(case.players, case.rounds, case.seed)
    play_out(game, Random(case.seed).choice)
    return game


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_a_match_comes_to_rest_once_it_has_played_the_rounds_it_was_built_for(case: MatchCase) -> None:
    game = a_match_played_out(case)

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert game.state.round_number == case.rounds
    assert game.state.to_act == frozenset()
    assert game.legal_moves(game.position) == ()
    assert game.settle() == ()


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_every_round_of_a_match_awards_the_point_it_is_worth(case: MatchCase) -> None:
    """A round goes to the shortest hand at the table, and there is always one of those, so none goes unscored."""
    game = a_match_played_out(case)

    assert sum(game.state.points) >= case.rounds * ROUND_POINT


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_a_match_runs_its_rounds_out_to_the_cards_it_was_dealt_from(case: MatchCase) -> None:
    game = a_match_played_out(case)
    stocked = len(game.board.zone(STOCK).cards)
    shed = len(game.board.zone(DISCARD).cards)
    held = sum(len(game.board.zone(hand_of(seat)).cards) for seat in range(case.players))

    assert stocked + shed + held == len(game.board.starting_deck)
    for seq in range(game.head + 1):
        game.snapshot(seq).board.validate_board()


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_the_memo_matches_a_replay_at_every_sequence_a_match_passes_through(case: MatchCase) -> None:
    game = a_match_played_out(case)

    assert all(game.snapshot(seq) == game.replay(seq) for seq in range(game.head + 1))


def test_a_decided_round_is_scored_into_the_standing_and_the_table_left_between_rounds(
    shedding: SheddingGame,
) -> None:
    hands = (A_PAIR, ONE_CARD, ANOTHER_CARD)
    position = a_table_of(shedding, hands, left_over(hands), ON_TURN)
    standing = position.state.points
    assert standing is not None

    out = shedding.step(position, a_shed(ON_TURN, frozenset({0, 1})), Random(SEED))
    closed = fold(shedding.close_round(out), out)

    assert out.state.phase == SheddingPhase.DECIDED
    assert closed.state.points == tuple(
        scored + award for scored, award in zip(standing, out.state.round_points, strict=True)
    )
    assert closed.state.phase == MatchPhase.BETWEEN_ROUNDS
    assert closed.state.to_act == frozenset()


def test_the_round_after_one_decided_is_dealt_to_the_next_seat_round_the_table(shedding: SheddingGame) -> None:
    leader = shedding.state.led_by

    while shedding.state.round_number == ONE_ROUND:
        moves = shedding.legal_moves(shedding.position)
        if moves:
            shedding.submit(moves[RUN_OUT], base_seq=shedding.head)
        else:
            shedding.settle()

    assert shedding.state.phase == SheddingPhase.SHEDDING
    assert shedding.state.led_by == (leader + 1) % SEATS
    assert shedding.state.winner is None
    assert shedding.state.round_points == (NOTHING,) * SEATS
    assert sum(shedding.state.points) >= ROUND_POINT


@given(seed=st.sampled_from(SEEDS))
@settings(deadline=None, max_examples=len(SEEDS))
def test_a_match_dealt_and_played_from_any_generator_runs_its_rounds_out(seed: int) -> None:
    game = a_match(SEATS, ROUNDS, seed)

    play_out(game, Random(seed).choice)

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert game.state.round_number == ROUNDS
    assert sum(game.state.points) >= ROUNDS * ROUND_POINT
    assert game.snapshot(game.head) == game.replay()
    for seq in range(game.head + 1):
        game.snapshot(seq).board.validate_board()
