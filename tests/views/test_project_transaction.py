from typing import Final

import pytest

from cardwork.effects.effects import AnyEffect, MoveCards, Reorder, SetState
from cardwork.moves.actions import Play
from cardwork.moves.move import Move
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.transactions.transaction import Transaction
from cardwork.views.event import EventView
from cardwork.views.project import project_transaction

from .conftest import ALSO_HELD_BY_ONE, HELD_BY_ONE

COMMIT_SEQ: Final[int] = 4
ARRANGEMENT: Final[Move] = Move(player=1, action=Play(group="table", indices=frozenset({0})))


def a_commit(
    position: Position[GameState], effect: AnyEffect[GameState], move: Move | None
) -> tuple[Transaction[GameState], Position[GameState]]:
    return Transaction(seq=COMMIT_SEQ, move=move, effects=(effect,)), effect.apply(position)


@pytest.fixture(name="played")
def played_fixture(position: Position[GameState]) -> tuple[Transaction[GameState], Position[GameState]]:
    return a_commit(
        position,
        MoveCards(source="hand:1", indices=frozenset({0}), target="discard", face_down=False),
        ARRANGEMENT,
    )


def test_project_transaction_reports_the_zones_the_commit_altered(
    position: Position[GameState], played: tuple[Transaction[GameState], Position[GameState]]
) -> None:
    transaction, after = played

    event = project_transaction(transaction, position, after, observer=0, legal=())

    assert tuple(change.zone for change in event.changes) == ("discard", "hand:1")


def test_project_transaction_leaves_untouched_zones_out(
    position: Position[GameState], played: tuple[Transaction[GameState], Position[GameState]]
) -> None:
    transaction, after = played

    event = project_transaction(transaction, position, after, observer=0, legal=())

    assert "draw" not in {change.zone for change in event.changes}


def test_project_transaction_shows_an_opponent_a_count_and_no_identities(
    position: Position[GameState], played: tuple[Transaction[GameState], Position[GameState]]
) -> None:
    transaction, after = played

    event = project_transaction(transaction, position, after, observer=0, legal=())

    hand = next(change for change in event.changes if change.zone == "hand:1")
    assert hand.before == (None, None)
    assert hand.after == (None,)


def test_project_transaction_shows_the_actor_their_own_cards(
    position: Position[GameState], played: tuple[Transaction[GameState], Position[GameState]]
) -> None:
    transaction, after = played

    event = project_transaction(transaction, position, after, observer=1, legal=())

    hand = next(change for change in event.changes if change.zone == "hand:1")
    assert hand.before == (HELD_BY_ONE, ALSO_HELD_BY_ONE)
    assert hand.after == (ALSO_HELD_BY_ONE,)


def test_project_transaction_shows_the_played_card_to_the_whole_table(
    position: Position[GameState], played: tuple[Transaction[GameState], Position[GameState]]
) -> None:
    transaction, after = played

    event = project_transaction(transaction, position, after, observer=0, legal=())

    discard = next(change for change in event.changes if change.zone == "discard")
    assert discard.after[-1] == HELD_BY_ONE.with_face(False)


def test_project_transaction_returns_the_action_to_the_seat_that_made_it(
    position: Position[GameState], played: tuple[Transaction[GameState], Position[GameState]]
) -> None:
    transaction, after = played

    event = project_transaction(transaction, position, after, observer=1, legal=())

    assert event.move is not None
    assert event.move.action == ARRANGEMENT.action


@pytest.mark.parametrize("observer", [0, 2, None], ids=["an opponent", "another opponent", "a spectator"])
def test_project_transaction_names_the_actor_and_withholds_the_action(
    observer: int | None, position: Position[GameState], played: tuple[Transaction[GameState], Position[GameState]]
) -> None:
    transaction, after = played

    event = project_transaction(transaction, position, after, observer, legal=())

    assert event.move is not None
    assert event.move.player == 1
    assert event.move.action is None


def test_project_transaction_carries_no_move_for_a_commit_the_engine_raised(position: Position[GameState]) -> None:
    transaction, after = a_commit(position, SetState(state=GameState(phase="score")), move=None)

    event = project_transaction(transaction, position, after, observer=0, legal=())

    assert event.move is None


def test_project_transaction_carries_the_cursor_the_commit_left(position: Position[GameState]) -> None:
    scored = GameState(phase="score", to_act=frozenset(), points=(3, 5, 1))
    transaction, after = a_commit(position, SetState(state=scored), move=None)

    assert project_transaction(transaction, position, after, observer=0, legal=()).state == scored


def test_project_transaction_stays_silent_about_a_shuffle_of_a_hidden_pile(position: Position[GameState]) -> None:
    transaction, after = a_commit(position, Reorder(zone="draw", order=(1, 0)), move=None)

    assert project_transaction(transaction, position, after, observer=0, legal=()).changes == ()


def test_project_transaction_reports_a_shuffle_of_a_pile_lying_face_up(position: Position[GameState]) -> None:
    face_up = position.board.with_zones(
        position.board.zone("draw").with_cards(
            tuple(card.with_face(False) for card in position.board.zone("draw").cards)
        )
    )
    exposed = position.with_board(face_up)
    transaction, after = a_commit(exposed, Reorder(zone="draw", order=(1, 0)), move=None)

    assert tuple(
        change.zone for change in project_transaction(transaction, exposed, after, observer=0, legal=()).changes
    ) == ("draw",)


def test_project_transaction_stamps_the_sequence_of_the_commit(
    position: Position[GameState], played: tuple[Transaction[GameState], Position[GameState]]
) -> None:
    transaction, after = played

    assert project_transaction(transaction, position, after, observer=0, legal=()).seq == COMMIT_SEQ


def test_project_transaction_round_trips_through_json(
    position: Position[GameState], played: tuple[Transaction[GameState], Position[GameState]]
) -> None:
    transaction, after = played
    event = project_transaction(transaction, position, after, observer=1, legal=())

    restored = EventView[GameState].model_validate_json(event.model_dump_json())

    assert restored == event
