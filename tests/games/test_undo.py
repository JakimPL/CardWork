from typing import Final

import pytest

from cardwork.exceptions import UndoUnavailable
from cardwork.moves.actions import Play
from cardwork.moves.move import Move

from .demo import DiscardGame

FIRST: Final[Move] = Move(player=0, action=Play(group="discard", indices=frozenset({0})))


def test_undo_returns_the_table_to_the_position_before_the_commit(game: DiscardGame) -> None:
    standing = game.position

    game.submit(FIRST, base_seq=game.head)
    game.undo()

    assert game.position == standing


def test_undo_drops_the_commit_from_the_record(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)
    game.undo()

    assert game.head == 1
    assert game.journal.transactions[-1].move is None


def test_undo_keeps_the_record_and_the_memo_in_step(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)
    game.undo()

    assert game.snapshot(game.head) == game.replay()


def test_a_move_may_be_submitted_again_once_it_has_been_undone(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)
    game.undo()

    assert game.submit(FIRST, base_seq=game.head).seq == 1


def test_undo_refuses_to_cross_what_the_table_has_published(game: DiscardGame) -> None:
    game.submit(FIRST, base_seq=game.head)
    game.mark_published()

    with pytest.raises(UndoUnavailable):
        game.undo()


def test_undo_reaches_a_commit_made_since_the_last_publication(game: DiscardGame) -> None:
    game.mark_published()
    game.submit(FIRST, base_seq=game.head)

    game.undo()

    assert game.head == 1


def test_undo_refuses_a_table_standing_at_its_deal(game: DiscardGame) -> None:
    game.mark_published()

    with pytest.raises(UndoUnavailable):
        game.undo()
