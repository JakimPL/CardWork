from random import Random
from typing import Final

import pytest

from cardwork.exceptions import IllegalMove, NotYourTurn, StalePosition
from cardwork.moves.actions import Discard, Play
from cardwork.moves.move import Move

from .conftest import SEED
from .demo import DECK, HAND_SIZE, SEATS, BareGame, DiscardGame, hand_of

FIRST: Final[Move] = Move(player=0, action=Play(group="discard", indices=frozenset({0})))


def test_submit_numbers_the_transaction_where_the_journal_stood(game: DiscardGame) -> None:
    assert game.submit(FIRST, base_seq=game.head).seq == 1


def test_submit_records_the_move_that_prompted_it(game: DiscardGame) -> None:
    assert game.submit(FIRST, base_seq=game.head).move == FIRST


def test_submit_carries_the_table_one_commit_onwards(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    assert game.head == 2


def test_submit_lays_the_card_face_up_on_the_discard(game: DiscardGame) -> None:
    played = game.board.zone(hand_of(0)).cards[0]

    game.submit(FIRST, base_seq=game.head)

    assert game.board.zone("discard").cards == (played.with_face(False),)


def test_submit_takes_the_acting_seat_out_of_the_round(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    assert game.state.to_act == frozenset({1, 2})


def test_submit_folds_the_move_and_its_turn_change_into_one_commit(game: DiscardGame) -> None:
    transaction = game.submit(FIRST, base_seq=game.head)

    assert len(transaction.effects) == 2


@pytest.mark.parametrize("base_seq", [0, 2], ids=["a position since superseded", "a position yet to be reached"])
def test_submit_refuses_a_move_built_on_another_position(game: DiscardGame, base_seq: int) -> None:
    with pytest.raises(StalePosition):
        game.submit(FIRST, base_seq=base_seq)


def test_submit_refuses_a_seat_that_has_already_acted(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    with pytest.raises(NotYourTurn):
        game.submit(FIRST, base_seq=game.head)


@pytest.mark.parametrize(
    "action",
    [
        pytest.param(Play(group="discard", indices=frozenset({HAND_SIZE})), id="a card the seat does not hold"),
        pytest.param(Play(group="discard", indices=frozenset({0, 1})), id="two cards at once"),
        pytest.param(Discard(group="discard", indices=frozenset({0})), id="an intent the game has no reading for"),
    ],
)
def test_submit_refuses_a_move_the_rules_reject(game: DiscardGame, action: Play | Discard) -> None:
    with pytest.raises(IllegalMove):
        game.submit(Move(player=0, action=action), base_seq=game.head)


def test_a_refused_move_leaves_the_table_where_it_stood(game: DiscardGame) -> None:
    standing = game.position

    with pytest.raises(IllegalMove):
        game.submit(Move(player=0, action=Play(group="discard", indices=frozenset({HAND_SIZE}))), base_seq=game.head)

    assert game.position == standing
    assert game.head == 1


def test_every_seat_may_act_while_the_round_stays_open(game: DiscardGame) -> None:
    for seat in range(SEATS):
        game.submit(Move(player=seat, action=Play(group="discard", indices=frozenset({0}))), base_seq=game.head)

    assert game.state.to_act == frozenset()
    assert len(game.board.zone("discard").cards) == SEATS


def test_step_returns_the_position_a_move_leads_to(game: DiscardGame) -> None:
    reached = game.step(game.position, FIRST, Random(SEED))

    assert len(reached.board.zone(hand_of(0)).cards) == HAND_SIZE - 1


def test_step_leaves_the_table_untouched(game: DiscardGame) -> None:
    standing = game.position

    game.step(game.position, FIRST, Random(SEED))

    assert game.position == standing
    assert game.head == 1


def test_step_puts_the_same_turn_policy_to_a_speculative_move(game: DiscardGame) -> None:
    with pytest.raises(NotYourTurn):
        game.step(game.step(game.position, FIRST, Random(SEED)), FIRST, Random(SEED))


def test_legal_moves_lists_a_play_for_every_card_of_every_seat_still_to_act(game: DiscardGame) -> None:
    assert len(game.legal_moves(game.position)) == SEATS * HAND_SIZE


def test_legal_moves_narrows_as_seats_act(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    assert {move.player for move in game.legal_moves(game.position)} == {1, 2}


def test_a_game_that_enumerates_nothing_offers_an_empty_list() -> None:
    game = BareGame(players=SEATS, deck=DECK, rng=Random(SEED))

    assert game.legal_moves(game.position) == ()
