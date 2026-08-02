from cardwork.boards.board import Board
from cardwork.games.state import GameState
from cardwork.models.base import BaseFrozen


class Position(BaseFrozen):
    board: Board
    state: GameState
