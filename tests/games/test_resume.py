from random import Random
from typing import Final

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cardwork.exceptions import GameValidationError, UndoUnavailable
from cardwork.games.game import Game
from cardwork.states.state import GameState
from cardwork.transactions.journal import Journal

from .demo import DECK, SEATS, DiscardGame, SealedRoundGame

RULES = [DiscardGame, SealedRoundGame]
RULE_IDS = ["a public round", "a sealed round"]

DEALT_FROM: Final[int] = 20260802
TAKEN_UP_FROM: Final[int] = 41
PICKED_BY: Final[int] = 7
A_SMALLER_TABLE: Final[int] = 2
OBSERVERS: Final[tuple[int | None, ...]] = (None, *range(SEATS))
FROM_THE_FIRST: Final[int] = 0


def a_table(rules: type[Game[GameState]], seed: int) -> Game[GameState]:
    """A fresh table of the given rules, dealt from a generator of that seed."""
    return rules(players=SEATS, deck=DECK, rng=Random(seed))


def played(game: Game[GameState], picking: Random) -> Game[GameState]:
    """Drive a table through a legal sequence until the rules bring it to rest."""
    while True:
        moves = game.legal_moves(game.position)
        if moves:
            game.submit(picking.choice(list(moves)), base_seq=game.head)
        elif not game.settle():
            return game


def a_table_played_out(rules: type[Game[GameState]]) -> Game[GameState]:
    """One table of the given rules driven to rest, which is the run a record is kept of."""
    return played(a_table(rules, DEALT_FROM), Random(PICKED_BY))


def taken_up(rules: type[Game[GameState]], record: Journal[GameState]) -> Game[GameState]:
    """A table built afresh and handed a record, as a run beginning where another left off builds one.

    The generator is another than the one the record was played from, since what a table taken up stands at
    is the record rather than the draw: a run reading a table back has drawn a seed of its own.
    """
    game = a_table(rules, TAKEN_UP_FROM)
    game.resume(record)
    return game


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
def test_a_table_taken_up_stands_where_the_record_it_was_handed_stood(rules: type[Game[GameState]]) -> None:
    played_out = a_table_played_out(rules)

    game = taken_up(rules, played_out.journal)

    assert game.head == played_out.head
    assert game.position == played_out.position
    assert game.journal == played_out.journal


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
@pytest.mark.parametrize("observer", OBSERVERS, ids=["a spectator", *(f"seat {seat}" for seat in range(SEATS))])
def test_a_table_taken_up_reads_to_every_observer_as_it_read_before(
    rules: type[Game[GameState]], observer: int | None
) -> None:
    """Both halves of what a client is served, since one joins on the view and follows on the stream."""
    played_out = a_table_played_out(rules)

    game = taken_up(rules, played_out.journal)

    assert game.view(observer) == played_out.view(observer)
    assert game.events(observer, since=FROM_THE_FIRST) == played_out.events(observer, since=FROM_THE_FIRST)


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
def test_a_table_taken_up_admits_the_moves_a_table_that_never_stopped_admits(rules: type[Game[GameState]]) -> None:
    played_out = a_table_played_out(rules)

    game = taken_up(rules, played_out.journal)

    assert game.legal_moves(game.position) == played_out.legal_moves(played_out.position)


def test_a_move_lands_on_a_table_taken_up_at_the_sequence_it_would_have_landed_at() -> None:
    """A table driven to a turn still to take, so the record it is taken up from leaves a move to make."""
    played_out = a_table(DiscardGame, DEALT_FROM)
    picking = Random(PICKED_BY)
    played_out.submit(picking.choice(list(played_out.legal_moves(played_out.position))), base_seq=played_out.head)

    game = taken_up(DiscardGame, played_out.journal)
    landed = game.submit(picking.choice(list(game.legal_moves(game.position))), base_seq=game.head)

    assert landed.seq == played_out.head
    assert game.head == played_out.head + 1


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
def test_a_table_taken_up_holds_every_commit_of_its_record_closed_to_undo(rules: type[Game[GameState]]) -> None:
    """Everything a record holds was served by the run that wrote it, so none of it is a table's to take back."""
    played_out = a_table_played_out(rules)

    game = taken_up(rules, played_out.journal)

    with pytest.raises(UndoUnavailable):
        game.undo()


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
def test_a_record_of_a_table_of_another_seating_is_refused(rules: type[Game[GameState]]) -> None:
    smaller = rules(players=A_SMALLER_TABLE, deck=DECK, rng=Random(DEALT_FROM))
    game = a_table(rules, DEALT_FROM)

    with pytest.raises(GameValidationError):
        game.resume(smaller.journal)


def test_a_record_kept_of_another_game_s_rules_is_refused() -> None:
    """The two demo games lay a table out differently, which is what their origins differ by."""
    sealed = a_table(SealedRoundGame, DEALT_FROM)
    game = a_table(DiscardGame, DEALT_FROM)

    with pytest.raises(GameValidationError):
        game.resume(sealed.journal)


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
def test_a_table_refusing_a_record_stands_where_it_stood(rules: type[Game[GameState]]) -> None:
    smaller = rules(players=A_SMALLER_TABLE, deck=DECK, rng=Random(DEALT_FROM))
    game = a_table(rules, DEALT_FROM)
    dealt = game.position

    with pytest.raises(GameValidationError):
        game.resume(smaller.journal)

    assert game.position == dealt
    assert game.head == 1


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
def test_a_record_travels_through_json_as_the_record_it_was(rules: type[Game[GameState]]) -> None:
    """What a run writes down and reads back is the record itself, which every resume rests on."""
    played_out = a_table_played_out(rules)

    written = played_out.journal.model_dump_json()
    read_back = Journal[GameState].model_validate_json(written)

    assert read_back == played_out.journal
    assert taken_up(rules, read_back).position == played_out.position


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
@given(data=st.data())
@settings(deadline=None, max_examples=50)
def test_the_memo_of_a_table_taken_up_matches_a_replay_at_every_sequence(
    rules: type[Game[GameState]], data: st.DataObject
) -> None:
    """The invariant every event rests on, held across a resume: each position is folded from the one before."""
    played_out = a_table(rules, data.draw(st.integers(min_value=0, max_value=9999)))
    while True:
        moves = played_out.legal_moves(played_out.position)
        if moves:
            played_out.submit(data.draw(st.sampled_from(moves)), base_seq=played_out.head)
        elif not played_out.settle():
            break

    game = taken_up(rules, played_out.journal)

    assert all(game.snapshot(seq) == game.replay(seq) for seq in range(game.head + 1))
