from random import Random

import pytest

from cardwork.games.game import SETTLE_LIMIT
from cardwork.moves.actions import Play
from cardwork.moves.move import Move

from .conftest import SEED
from .demo import DECK, SEATS, DiscardGame, EndlessGame, hand_of


def close_the_round(game: DiscardGame) -> None:
    for seat in range(SEATS):
        game.submit(Move(player=seat, action=Play(group="discard", indices=frozenset({0}))), base_seq=game.head)


def test_settle_leaves_a_table_still_in_its_round_alone(game: DiscardGame) -> None:
    assert game.settle() == ()
    assert game.head == 1


def test_settle_closes_a_round_whose_last_seat_has_acted(game: DiscardGame) -> None:
    close_the_round(game)

    settled = game.settle()

    assert len(settled) == 1
    assert game.state.phase == "score"


def test_a_settling_commit_carries_no_move(game: DiscardGame) -> None:
    close_the_round(game)

    assert game.settle()[0].move is None


def test_settle_numbers_its_commits_where_the_journal_stood(game: DiscardGame) -> None:
    close_the_round(game)
    standing = game.head

    assert game.settle()[0].seq == standing


def test_settle_scores_the_seats(game: DiscardGame) -> None:
    close_the_round(game)

    game.settle()

    assert game.state.points == tuple(len(game.board.zone(hand_of(seat)).cards) for seat in range(SEATS))


def test_settle_comes_to_rest(game: DiscardGame) -> None:
    close_the_round(game)
    game.settle()

    assert game.settle() == ()


def test_settle_stops_a_game_whose_rules_go_round_in_a_circle() -> None:
    game = EndlessGame(players=SEATS, deck=DECK, rng=Random(SEED))

    with pytest.raises(RuntimeError):
        game.settle()


def test_a_circling_game_settles_exactly_as_far_as_the_cap_allows() -> None:
    game = EndlessGame(players=SEATS, deck=DECK, rng=Random(SEED))
    standing = game.head

    with pytest.raises(RuntimeError):
        game.settle()

    assert game.head == standing + SETTLE_LIMIT
