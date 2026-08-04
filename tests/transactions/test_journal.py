from typing import Final

import pytest

from cardwork.boards.board import Board
from cardwork.cards.card import Card
from cardwork.cards.game import GameCard
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.effects.effects import AnyEffect, MoveCards, SetState
from cardwork.exceptions import UndoUnavailable
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.transactions.journal import Journal
from cardwork.transactions.transaction import Transaction
from cardwork.zones.presets import HAND, PILE
from cardwork.zones.zone import Zone

PLAYERS: Final[int] = 2
HELD: Final[GameCard] = GameCard(card=Card(rank=Rank.ACE, suit=Suit.SPADE), face_down=True)
ALSO_HELD: Final[GameCard] = GameCard(card=Card(rank=Rank.KING, suit=Suit.HEART), face_down=True)

LAY_DOWN: Final[AnyEffect[GameState]] = MoveCards(
    source="hand:0", indices=frozenset({0}), target="discard", face_down=False
)
SCORE: Final[AnyEffect[GameState]] = SetState(state=GameState(phase="score", points=(1, 0)))


@pytest.fixture(name="origin")
def origin_fixture() -> Position[GameState]:
    return Position(
        board=Board(
            starting_deck=(HELD.card, ALSO_HELD.card),
            zones={
                "hand:0": Zone(id="hand:0", owner=0, visibility=HAND, ordered=False, cards=(HELD, ALSO_HELD)),
                "discard": Zone(
                    id="discard",
                    visibility=PILE,
                    ordered=True,
                ),
            },
        ),
        state=GameState(phase="play", to_act=frozenset({0})),
        players=PLAYERS,
    )


@pytest.fixture(name="journal")
def journal_fixture(origin: Position[GameState]) -> Journal[GameState]:
    return Journal(initial=origin).append(Transaction(seq=0, move=None, effects=(LAY_DOWN,)))


def test_a_fresh_journal_stands_at_its_origin(origin: Position[GameState]) -> None:
    assert Journal(initial=origin).head == 0


def test_head_counts_the_commits(journal: Journal[GameState]) -> None:
    assert journal.head == 1


def test_append_records_the_transaction_at_the_head(journal: Journal[GameState]) -> None:
    closing = Transaction(seq=1, move=None, effects=(SCORE,))

    assert journal.append(closing).transactions[-1] == closing


def test_append_leaves_the_journal_it_was_given_untouched(journal: Journal[GameState]) -> None:
    journal.append(Transaction(seq=1, move=None, effects=(SCORE,)))

    assert journal.head == 1


@pytest.mark.parametrize("seq", [0, 2, 7], ids=["a sequence already recorded", "a gap", "a distant gap"])
def test_append_rejects_a_transaction_numbered_off_the_head(journal: Journal[GameState], seq: int) -> None:
    with pytest.raises(ValueError):
        journal.append(Transaction(seq=seq, move=None, effects=(SCORE,)))


def test_truncate_drops_the_most_recent_commit(journal: Journal[GameState]) -> None:
    assert journal.append(Transaction(seq=1, move=None, effects=(SCORE,))).truncate() == journal


def test_truncate_refuses_a_journal_standing_at_its_origin(origin: Position[GameState]) -> None:
    with pytest.raises(UndoUnavailable):
        Journal(initial=origin).truncate()


def test_replay_of_nothing_returns_the_origin(journal: Journal[GameState], origin: Position[GameState]) -> None:
    assert journal.replay(0) == origin


def test_replay_folds_every_recorded_effect(journal: Journal[GameState]) -> None:
    replayed = journal.append(Transaction(seq=1, move=None, effects=(SCORE,))).replay()

    assert replayed.board.zone("discard").cards == (HELD.with_face(False),)
    assert replayed.state.phase == "score"


def test_replay_stops_where_it_is_asked_to(journal: Journal[GameState]) -> None:
    replayed = journal.append(Transaction(seq=1, move=None, effects=(SCORE,))).replay(1)

    assert replayed.state.phase == "play"


def test_a_journal_round_trips_through_json(journal: Journal[GameState]) -> None:
    restored = Journal[GameState].model_validate_json(journal.model_dump_json())

    assert restored == journal
