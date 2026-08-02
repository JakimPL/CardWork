from typing import Final, Self

import pytest

from cardwork.boards.board import Board
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.transactions.transaction import Transaction
from cardwork.views.project import project_position, project_transaction

from .conftest import PLAYERS, SEQ

BIDS: Final[tuple[int | None, ...]] = (3, 5, None)


class SealedBidState(GameState):
    """A cursor holding what each seat committed during a simultaneous round, sealed until the reveal."""

    bids: tuple[int | None, ...]

    def project(self, observer: int | None) -> Self:
        return self.with_changes(bids=tuple(bid if seat == observer else None for seat, bid in enumerate(self.bids)))


@pytest.fixture(name="bidding")
def bidding_fixture(board: Board) -> Position[SealedBidState]:
    return Position(
        board=board,
        state=SealedBidState(phase="bid", to_act=frozenset({2}), bids=BIDS),
        players=PLAYERS,
    )


def test_a_state_returns_the_bid_of_the_seat_that_made_it(bidding: Position[SealedBidState]) -> None:
    assert bidding.state.project(0).bids == (3, None, None)


def test_a_state_seals_every_bid_from_a_spectator(bidding: Position[SealedBidState]) -> None:
    assert bidding.state.project(None).bids == (None, None, None)


def test_a_state_carries_its_shared_cursor_fields_through_a_projection(bidding: Position[SealedBidState]) -> None:
    projected = bidding.state.project(1)

    assert projected.phase == "bid"
    assert projected.to_act == frozenset({2})


def test_a_position_view_carries_the_cursor_the_state_projects(bidding: Position[SealedBidState]) -> None:
    view = project_position(bidding, SEQ, 1)

    assert view.state.bids == (None, 5, None)


def test_an_event_view_carries_the_cursor_the_state_projects(bidding: Position[SealedBidState]) -> None:
    transaction: Transaction[SealedBidState] = Transaction(seq=SEQ, move=None, effects=())

    event = project_transaction(transaction, bidding, bidding, observer=0)

    assert event.state.bids == (3, None, None)


def test_projecting_a_position_leaves_the_sealed_bids_on_the_server(bidding: Position[SealedBidState]) -> None:
    project_position(bidding, SEQ, 1)

    assert bidding.state.bids == BIDS
