from typing import Generic

from pydantic import Field

from cardwork.boards.board import Board
from cardwork.models.base import BaseFrozen
from cardwork.states.state import StateT


class Position(BaseFrozen, Generic[StateT]):
    """A complete snapshot of a table: every card, the rules cursor, and how many seats are in play.

    Carrying the seat count keeps any position projectable on its own, including one recovered from
    `Journal.replay`, which is what makes "what did player 1 see at move 17?" answerable.
    """

    board: Board
    state: StateT
    players: int = Field(ge=1)

    def with_board(self, board: Board) -> "Position[StateT]":
        return Position(board=board, state=self.state, players=self.players)

    def with_state(self, state: StateT) -> "Position[StateT]":
        return Position(board=self.board, state=state, players=self.players)
