from typing import Final

import pytest

from cardwork.moves.actions import Play
from cardwork.moves.move import Move

from .demo import HAND_SIZE, SEATS, DiscardGame, hand_of

FIRST: Final[Move] = Move(player=0, action=Play(group="discard", indices=frozenset({0})))
SECOND: Final[Move] = Move(player=1, action=Play(group="discard", indices=frozenset({0})))
DEAL: Final[int] = 1


def test_view_stamps_the_sequence_the_table_stands_at(game: DiscardGame) -> None:
    assert game.view(observer=0).seq == game.head


def test_view_hands_a_seat_its_own_cards(game: DiscardGame) -> None:
    assert game.view(observer=0).zones[hand_of(0)].cards == game.board.zone(hand_of(0)).cards


def test_view_keeps_a_seat_out_of_another_hand(game: DiscardGame) -> None:
    assert game.view(observer=0).zones[hand_of(1)].cards == (None,) * HAND_SIZE


def test_view_narrows_a_spectator_to_the_public_table(game: DiscardGame) -> None:
    view = game.view(observer=None)

    assert all(view.zones[hand_of(seat)].cards == (None,) * HAND_SIZE for seat in range(SEATS))


def test_view_carries_the_cursor(game: DiscardGame) -> None:
    assert game.view(observer=0).state == game.state


def test_view_offers_a_seat_one_move_for_every_card_it_holds(game: DiscardGame) -> None:
    assert len(game.view(observer=0).legal) == HAND_SIZE


def test_view_offers_a_seat_no_move_of_another_while_the_whole_table_owes_one(game: DiscardGame) -> None:
    assert all(move.player == 1 for move in game.view(observer=1).legal)


def test_view_offers_a_spectator_no_move(game: DiscardGame) -> None:
    assert game.view(observer=None).legal == ()


def test_view_offers_nothing_to_a_seat_that_has_acted(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    assert game.view(observer=0).legal == ()


def test_events_report_every_commit_from_the_deal_onwards(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    assert tuple(event.seq for event in game.events(observer=0, since=0)) == (0, 1)


def test_events_resume_where_a_client_dropped(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    assert tuple(event.seq for event in game.events(observer=0, since=DEAL)) == (1,)


def test_events_run_dry_once_a_client_has_read_them_all(game: DiscardGame) -> None:
    assert game.events(observer=0, since=game.head) == ()


def test_events_name_the_seat_they_were_projected_for(game: DiscardGame) -> None:
    assert all(event.observer == 2 for event in game.events(observer=2, since=0))


def test_an_event_reports_the_seat_that_acted(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    move = game.events(observer=1, since=DEAL)[0].move
    assert move is not None
    assert move.player == 0


def test_an_event_shows_an_opponent_a_count_where_a_card_had_been(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    change = next(change for change in game.events(observer=1, since=DEAL)[0].changes if change.zone == hand_of(0))
    assert change.before == (None,) * HAND_SIZE
    assert change.after == (None,) * (HAND_SIZE - 1)


def test_an_event_shows_the_actor_the_card_it_laid_down(game: DiscardGame) -> None:
    laid = game.board.zone(hand_of(0)).cards[0]

    game.submit(FIRST, base_seq=game.head)

    change = next(change for change in game.events(observer=0, since=DEAL)[0].changes if change.zone == "discard")
    assert change.after == (laid.with_face(False),)


def test_an_event_offers_the_moves_the_commit_it_reports_left_open(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    assert len(game.events(observer=1, since=DEAL)[0].legal) == HAND_SIZE


def test_an_event_offers_the_moves_of_the_position_it_produced_rather_than_of_the_table_now(
    game: DiscardGame,
) -> None:
    game.submit(FIRST, base_seq=game.head)
    game.submit(SECOND, base_seq=game.head)

    laid, followed = game.events(observer=1, since=DEAL)

    assert len(laid.legal) == HAND_SIZE
    assert followed.legal == ()


def test_events_reject_a_sequence_below_the_start_of_the_record(game: DiscardGame) -> None:
    with pytest.raises(ValueError):
        game.events(observer=0, since=-1)


def test_snapshot_returns_the_position_the_table_stood_at(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)

    assert game.snapshot(game.head) == game.position


@pytest.mark.parametrize("seq", [-1, 2], ids=["a point before the origin", "a point yet to be reached"])
def test_snapshot_refuses_a_point_outside_the_record(game: DiscardGame, seq: int) -> None:
    with pytest.raises(IndexError):
        game.snapshot(seq)
