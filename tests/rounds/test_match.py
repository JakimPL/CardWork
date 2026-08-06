from random import Random
from typing import Final

from cardwork.rounds.conclusion import Conclusion
from cardwork.rounds.state import MatchPhase
from cardwork.states.state import Points
from cardwork.transactions.transaction import Transactions

from .demo import (
    DECK,
    HAND_SIZE,
    ROUNDS,
    SEATS,
    SEED,
    CountedTossGame,
    MatchState,
    TossGame,
    TossPhase,
    UnscoredGame,
    WinnerGame,
    a_match,
    hand_of,
    toss_a_card,
    toss_the_round,
)

SEEDS = range(12)
TARGET: Final[int] = 100
A_SHORT_TARGET: Final[int] = 12
A_SHORT_LEAD: Final[int] = 2
LONG_ENOUGH: Final[int] = 40
LEADING: Final[int] = 0
CHASING: Final[int] = 1


def first_leader(seed: int) -> int:
    """The seat a table drawing from this seed opens its first round on."""
    return a_match(TossGame, seed, ROUNDS).state.led_by


def closing(settled: Transactions[MatchState]) -> MatchState:
    """The cursor left by the first of the settled transactions, which is the one closing a round."""
    return settled[0].effects[-1].state


def played_out(game: TossGame) -> tuple[Points, ...]:
    """The match driven to its close, answering with the tally each of its rounds scored."""
    tallies: list[Points] = []
    while game.state.phase != MatchPhase.MATCH_OVER:
        toss_the_round(game)
        tallies.append(game.state.round_points)
        game.settle()

    return tuple(tallies)


def test_a_fresh_table_stands_in_a_first_round_dealt_and_led(toss: TossGame) -> None:
    state = toss.state

    assert state.phase == TossPhase.TOSSING
    assert state.round_number == 1
    assert state.leader in range(SEATS)
    assert state.to_act == frozenset({state.led_by})
    assert state.round_points == (0,) * SEATS
    assert state.points == (0,) * SEATS
    assert all(len(toss.board.zone(hand_of(seat)).cards) == HAND_SIZE for seat in range(SEATS))


def test_the_deal_of_the_first_round_and_the_cursor_it_opens_land_in_one_transaction(toss: TossGame) -> None:
    opening = toss.journal.transactions[0]

    assert opening.seq == 0
    assert opening.move is None
    assert tuple(effect.kind for effect in opening.effects) == ("reorder",) + ("move_cards",) * SEATS + ("set_state",)


def test_the_seats_toss_in_turn_counting_on_from_the_leader(toss: TossGame) -> None:
    leader = toss.state.led_by

    turns = []
    while toss.state.to_act:
        turns.append(toss.state.current)
        toss_a_card(toss)

    assert turns == [(leader + place) % SEATS for place in range(SEATS)]


def test_a_round_that_has_run_out_is_scored_into_the_standing(toss: TossGame) -> None:
    toss_the_round(toss)
    tally = toss.state.round_points

    closed = closing(toss.settle())

    assert closed.phase == MatchPhase.BETWEEN_ROUNDS
    assert closed.to_act == frozenset()
    assert closed.points == tally
    assert closed.round_points == tally


def test_the_boundary_between_two_rounds_is_two_transactions_no_seat_asked_for(toss: TossGame) -> None:
    toss_the_round(toss)

    settled = toss.settle()

    assert len(settled) == 2
    assert all(transaction.move is None for transaction in settled)
    assert closing(settled).phase == MatchPhase.BETWEEN_ROUNDS
    assert toss.state.phase == TossPhase.TOSSING


def test_the_round_after_one_is_led_by_the_seat_after_its_leader(toss: TossGame) -> None:
    leader = toss.state.led_by
    toss_the_round(toss)

    toss.settle()

    assert toss.state.round_number == 2
    assert toss.state.led_by == (leader + 1) % SEATS
    assert toss.state.round_points == (0,) * SEATS
    assert all(len(toss.board.zone(hand_of(seat)).cards) == HAND_SIZE for seat in range(SEATS))


def test_the_first_leader_is_drawn_afresh_and_stands_the_same_under_one_seed() -> None:
    assert first_leader(SEED) == first_leader(SEED)
    assert {first_leader(seed) for seed in SEEDS} == set(range(SEATS))


def test_a_match_closes_once_it_has_played_the_rounds_it_was_built_for(toss: TossGame) -> None:
    tallies = played_out(toss)

    assert toss.state.phase == MatchPhase.MATCH_OVER
    assert toss.state.round_number == ROUNDS
    assert toss.state.to_act == frozenset()
    assert toss.state.points == tuple(sum(tally[seat] for tally in tallies) for seat in range(SEATS))
    assert toss.legal_moves(toss.position) == ()
    assert toss.settle() == ()


def test_a_match_counting_rounds_won_awards_each_round_to_its_highest_tally() -> None:
    game = a_match(WinnerGame, SEED, ROUNDS)

    tallies = played_out(game)

    assert game.state.points == tuple(sum(int(tally[seat] == max(tally)) for tally in tallies) for seat in range(SEATS))
    assert sum(game.state.points) >= ROUNDS


def test_a_round_owing_a_step_of_its_own_is_carried_through_it_before_the_boundary_closes_it() -> None:
    game = a_match(CountedTossGame, SEED, ROUNDS)
    toss_the_round(game)

    settled = game.settle()

    assert tuple(transaction.effects[-1].state.phase for transaction in settled) == (
        TossPhase.COUNTING,
        MatchPhase.BETWEEN_ROUNDS,
        TossPhase.TOSSING,
    )
    assert all(transaction.move is None for transaction in settled)


def test_a_match_that_states_no_standing_takes_the_tally_of_its_first_round_as_one() -> None:
    game = a_match(UnscoredGame, SEED, ROUNDS)
    toss_the_round(game)
    tally = game.state.round_points

    closed = closing(game.settle())

    assert closed.points == tally


def test_a_match_of_one_round_closes_on_that_round() -> None:
    game = TossGame(players=SEATS, deck=DECK, conclusion=Conclusion(rounds=1), rng=Random(SEED))

    toss_the_round(game)
    game.settle()

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert game.state.round_number == 1


def test_the_table_a_match_opens_on_carries_the_clauses_it_runs_to() -> None:
    game = TossGame(players=SEATS, deck=DECK, conclusion=Conclusion(target=TARGET), rng=Random(SEED))

    assert game.snapshot(0).state.rounds is None
    assert game.snapshot(0).state.target == TARGET
    assert game.state.target == TARGET


def test_a_match_to_a_score_closes_once_a_seat_reaches_it() -> None:
    game = TossGame(players=SEATS, deck=DECK, conclusion=Conclusion(target=A_SHORT_TARGET), rng=Random(SEED))

    while game.state.phase != MatchPhase.MATCH_OVER:
        toss_the_round(game)
        game.settle()

    assert max(game.state.points) >= A_SHORT_TARGET
    assert game.state.round_number < LONG_ENOUGH
    assert game.settle() == ()


def test_a_match_to_a_lead_closes_once_one_seat_pulls_that_far_clear() -> None:
    game = WinnerGame(players=SEATS, deck=DECK, conclusion=Conclusion(lead=A_SHORT_LEAD), rng=Random(SEED))

    while game.state.phase != MatchPhase.MATCH_OVER:
        toss_the_round(game)
        game.settle()

    standing = sorted(game.state.points, reverse=True)

    assert standing[LEADING] - standing[CHASING] >= A_SHORT_LEAD
    assert game.settle() == ()
