from random import Random
from typing import Final

import pytest

from cardgames.backend.showdown.game import ShowdownGame
from cardgames.backend.showdown.rules import (
    BLIND_SIZE,
    HAND_SIZE,
    NOTHING,
    ONE_CARD,
    TURNS,
)
from cardgames.backend.showdown.zones import DISCARD, Holding, blind_of, tray_of
from cardwork.exceptions import IllegalMove, NotYourTurn
from cardwork.moves.actions import Play, Take
from cardwork.moves.move import Move

from .driving import (
    FIRST_CARD,
    SEATS,
    SEED,
    commit,
    commit_the_turn,
    every_zone,
    held_by,
    holding_of,
    sealed_by,
)

FIRST_SEAT: Final[int] = 0
SECOND_SEAT: Final[int] = 1
ONE_SEAT: Final[int] = 1
BEYOND_THE_HAND: Final[int] = HAND_SIZE
SEALED: Final[int] = 1
UNKNOWN_HOLDING: Final[str] = "sleeve"


def test_a_commitment_seals_the_card_in_the_seats_own_tray_and_takes_the_seat_out_of_the_turn(
    showdown: ShowdownGame,
) -> None:
    chosen = held_by(showdown, FIRST_SEAT)[FIRST_CARD]

    commit(showdown, FIRST_SEAT, Holding.HAND, FIRST_CARD)

    assert sealed_by(showdown, FIRST_SEAT) == (chosen,)
    assert showdown.board.zone(tray_of(FIRST_SEAT)).cards[FIRST_CARD].face_down
    assert len(held_by(showdown, FIRST_SEAT)) == HAND_SIZE - ONE_CARD
    assert chosen not in held_by(showdown, FIRST_SEAT)
    assert showdown.state.to_act == frozenset(range(SEATS)) - {FIRST_SEAT}
    assert showdown.board.zone(DISCARD).cards == ()


def test_a_commitment_from_the_blind_takes_the_card_by_position_and_leaves_it_unread(showdown: ShowdownGame) -> None:
    commit(showdown, FIRST_SEAT, Holding.BLIND, FIRST_CARD)

    view = showdown.view(observer=FIRST_SEAT)

    assert len(holding_of(showdown, FIRST_SEAT, Holding.BLIND)) == BLIND_SIZE - ONE_CARD
    assert len(sealed_by(showdown, FIRST_SEAT)) == SEALED
    assert all(card is None for card in view.zones[tray_of(FIRST_SEAT)].cards)
    assert all(card is None for card in view.zones[blind_of(FIRST_SEAT)].cards)


def test_a_sealed_commitment_reads_to_nobody_and_its_size_to_everybody(showdown: ShowdownGame) -> None:
    commit(showdown, FIRST_SEAT, Holding.HAND, FIRST_CARD)

    for observer in (*range(SEATS), None):
        view = showdown.view(observer=observer)

        assert all(card is None for card in view.zones[tray_of(FIRST_SEAT)].cards)
        assert len(view.zones[tray_of(FIRST_SEAT)].cards) == SEALED
        assert len(view.zones[tray_of(SECOND_SEAT)].cards) == NOTHING


def test_the_turn_stands_open_while_a_seat_has_yet_to_commit(showdown: ShowdownGame) -> None:
    commit(showdown, FIRST_SEAT, Holding.HAND, FIRST_CARD)

    settled = showdown.settle()

    assert settled == ()
    assert showdown.board.zone(DISCARD).cards == ()
    assert showdown.state.round_points == (NOTHING,) * SEATS
    assert showdown.state.to_act == frozenset(range(SEATS)) - {FIRST_SEAT}


def test_a_second_commitment_in_one_turn_is_refused_and_leaves_the_table_as_it_stood(showdown: ShowdownGame) -> None:
    commit(showdown, FIRST_SEAT, Holding.HAND, FIRST_CARD)
    standing, table, head = showdown.state, every_zone(showdown), showdown.head

    with pytest.raises(NotYourTurn):
        commit(showdown, FIRST_SEAT, Holding.HAND, FIRST_CARD)

    assert showdown.state == standing
    assert every_zone(showdown) == table
    assert showdown.head == head


def test_a_commitment_from_a_holding_this_game_leaves_out_is_refused_and_leaves_the_table_as_it_stood(
    showdown: ShowdownGame,
) -> None:
    standing, table, head = showdown.state, every_zone(showdown), showdown.head

    with pytest.raises(IllegalMove, match="commits from its hand or its blind"):
        showdown.submit(
            Move(player=FIRST_SEAT, action=Play(group=UNKNOWN_HOLDING, indices=frozenset({FIRST_CARD}))),
            base_seq=showdown.head,
        )

    assert showdown.state == standing
    assert every_zone(showdown) == table
    assert showdown.head == head


def test_committing_two_cards_at_once_is_refused(showdown: ShowdownGame) -> None:
    with pytest.raises(IllegalMove, match="one card at a time"):
        showdown.submit(
            Move(
                player=FIRST_SEAT,
                action=Play(group=Holding.HAND, indices=frozenset({FIRST_CARD, ONE_CARD})),
            ),
            base_seq=showdown.head,
        )


def test_naming_a_position_the_holding_does_not_hold_is_refused(showdown: ShowdownGame) -> None:
    with pytest.raises(IllegalMove, match=f"of a hand holding {HAND_SIZE}"):
        commit(showdown, FIRST_SEAT, Holding.HAND, BEYOND_THE_HAND)


def test_committing_from_a_holding_that_has_run_out_is_refused(showdown: ShowdownGame) -> None:
    for _ in range(HAND_SIZE):
        commit_the_turn(showdown, Holding.HAND)

    with pytest.raises(IllegalMove, match=f"of a hand holding {NOTHING}"):
        commit(showdown, FIRST_SEAT, Holding.HAND, FIRST_CARD)


def test_an_intent_this_game_leaves_out_is_refused(showdown: ShowdownGame) -> None:
    with pytest.raises(IllegalMove, match="commits one card, and offered take"):
        showdown.submit(
            Move(player=FIRST_SEAT, action=Take(group=DISCARD, indices=frozenset({FIRST_CARD}))),
            base_seq=showdown.head,
        )


def test_the_moves_listed_are_every_card_of_both_holdings_of_every_seat_still_to_commit(
    showdown: ShowdownGame,
) -> None:
    moves = showdown.legal_moves(showdown.position)

    assert len(moves) == SEATS * TURNS
    assert {move.player for move in moves} == set(range(SEATS))
    assert all(isinstance(move.action, Play) for move in moves)
    assert len(tuple(move for move in moves if move.action.group == Holding.HAND)) == SEATS * HAND_SIZE
    assert len(tuple(move for move in moves if move.action.group == Holding.BLIND)) == SEATS * BLIND_SIZE


def test_a_seat_that_has_committed_leaves_the_list_to_the_seats_that_have_not(showdown: ShowdownGame) -> None:
    commit(showdown, FIRST_SEAT, Holding.HAND, FIRST_CARD)

    moves = showdown.legal_moves(showdown.position)

    assert {move.player for move in moves} == set(range(SEATS)) - {FIRST_SEAT}
    assert len(moves) == (SEATS - ONE_SEAT) * TURNS


def test_every_move_listed_is_one_the_rules_carry_through(showdown: ShowdownGame) -> None:
    for move in showdown.legal_moves(showdown.position):
        showdown.step(showdown.position, move, Random(SEED))

    assert showdown.head == showdown.journal.head
