from random import Random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cardwork.cards.game import GameCard
from cardwork.games.game import Game
from cardwork.states.state import GameState
from cardwork.zones.zone import ZoneId

from .demo import DECK, SEATS, DiscardGame, SealedRoundGame

RULES = [DiscardGame, SealedRoundGame]
RULE_IDS = ["a public round", "a sealed round"]


def a_table(rules: type[Game[GameState]], data: st.DataObject) -> Game[GameState]:
    """A fresh table of the given rules, dealt from a generator the example chose."""
    return rules(players=SEATS, deck=DECK, rng=Random(data.draw(st.integers(min_value=0, max_value=9999))))


def play_out(game: Game[GameState], data: st.DataObject) -> None:
    """Drive a table through a legal sequence the example chose, until the rules bring it to rest."""
    while True:
        moves = game.legal_moves(game.position)
        if moves:
            game.submit(data.draw(st.sampled_from(moves)), base_seq=game.head)
        elif not game.settle():
            return


def streamed(game: Game[GameState], observer: int | None) -> dict[ZoneId, tuple[GameCard | None, ...]]:
    """The table as a client holds it after reading every event, zone by zone."""
    return {change.zone: change.after for event in game.events(observer, since=0) for change in event.changes}


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
@given(data=st.data())
@settings(deadline=None, max_examples=50)
def test_the_memo_matches_a_replay_at_every_sequence(rules: type[Game[GameState]], data: st.DataObject) -> None:
    game = a_table(rules, data)

    play_out(game, data)

    assert all(game.snapshot(seq) == game.replay(seq) for seq in range(game.head + 1))


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
@given(data=st.data())
@settings(deadline=None, max_examples=50)
def test_the_memo_matches_a_replay_after_the_record_is_wound_back(
    rules: type[Game[GameState]], data: st.DataObject
) -> None:
    game = a_table(rules, data)
    play_out(game, data)

    for _ in range(data.draw(st.integers(min_value=0, max_value=game.head))):
        game.undo()

    assert all(game.snapshot(seq) == game.replay(seq) for seq in range(game.head + 1))


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
@given(data=st.data())
@settings(deadline=None, max_examples=50)
def test_every_position_the_table_reached_holds_the_deck_it_started_from(
    rules: type[Game[GameState]], data: st.DataObject
) -> None:
    game = a_table(rules, data)

    play_out(game, data)

    for seq in range(game.head + 1):
        game.snapshot(seq).board.validate_board()


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
@given(data=st.data(), observer=st.one_of(st.none(), st.integers(min_value=0, max_value=SEATS - 1)))
@settings(deadline=None, max_examples=50)
def test_reading_the_stream_leaves_a_client_where_a_fresh_view_would(
    rules: type[Game[GameState]], data: st.DataObject, observer: int | None
) -> None:
    game = a_table(rules, data)
    play_out(game, data)

    held = streamed(game, observer)
    view = game.view(observer)

    assert all(held.get(zone_id, ()) == zone.cards for zone_id, zone in view.zones.items())


@pytest.mark.parametrize("rules", RULES, ids=RULE_IDS)
@given(data=st.data())
@settings(deadline=None, max_examples=50)
def test_a_round_played_out_comes_to_rest_with_every_seat_scored(
    rules: type[Game[GameState]], data: st.DataObject
) -> None:
    game = a_table(rules, data)

    play_out(game, data)

    assert game.state.phase == "score"
    assert game.state.points is not None
    assert len(game.state.points) == SEATS
