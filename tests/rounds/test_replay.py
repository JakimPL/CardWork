from random import Random
from typing import Final

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cardwork.rounds.conclusion import Conclusion
from cardwork.rounds.state import MatchPhase

from .demo import DECK, SEATS, CountedTossGame, TossGame, WinnerGame

RULES = [TossGame, WinnerGame, CountedTossGame]
RULE_IDS = ["points scored", "rounds won", "a counted round"]
LONG_MATCH: Final[int] = 4


def a_match(rules: type[TossGame], data: st.DataObject) -> TossGame:
    """A fresh match of the given rules, drawing from a generator the example chose."""
    seed = data.draw(st.integers(min_value=0, max_value=9999))
    return rules(players=SEATS, deck=DECK, conclusion=Conclusion(rounds=LONG_MATCH), rng=Random(seed))


def play_out(game: TossGame, data: st.DataObject) -> None:
    """Drive a match through a legal sequence the example chose, until the rules bring it to rest."""
    while True:
        moves = game.legal_moves(game.position)
        if moves:
            game.submit(data.draw(st.sampled_from(moves)), base_seq=game.head)
        elif not game.settle():
            return


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
@given(data=st.data())
@settings(deadline=None, max_examples=25)
def test_the_memo_matches_a_replay_at_every_sequence_a_match_passes_through(
    rules: type[TossGame], data: st.DataObject
) -> None:
    game = a_match(rules, data)

    play_out(game, data)

    assert all(game.snapshot(seq) == game.replay(seq) for seq in range(game.head + 1))


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
@given(data=st.data())
@settings(deadline=None, max_examples=25)
def test_every_position_a_match_reached_holds_the_deck_it_started_from(
    rules: type[TossGame], data: st.DataObject
) -> None:
    game = a_match(rules, data)

    play_out(game, data)

    for seq in range(game.head + 1):
        game.snapshot(seq).board.validate_board()


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
@given(data=st.data())
@settings(deadline=None, max_examples=25)
def test_a_match_played_out_closes_with_every_round_scored(rules: type[TossGame], data: st.DataObject) -> None:
    game = a_match(rules, data)

    play_out(game, data)

    assert game.state.phase == MatchPhase.MATCH_OVER
    assert game.state.round_number == LONG_MATCH
    assert game.state.points is not None
    assert sum(game.state.points) > 0
