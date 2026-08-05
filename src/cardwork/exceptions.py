class CardworkError(Exception):
    """Root of the framework's error hierarchy.

    Adapters catch this single type to separate a rejected request from a defect in their own code.
    """


class IllegalMove(CardworkError):
    """Raised when the rules reject the content of a move."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class LogicError(CardworkError):
    """Raised when a move is built on a position that the rules reject."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class GameValidationError(CardworkError):
    """Raised when a game is constructed with parameters the rules reject."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class NotYourTurn(CardworkError):
    """Raised when a player submits a move while the turn belongs to other seats."""

    def __init__(self, player: int, to_act: frozenset[int]) -> None:
        super().__init__(f"Player {player} submitted while the turn belongs to {sorted(to_act)}")
        self.player = player
        self.to_act = to_act


class ArrangementRefused(CardworkError):
    """Raised when a seat asks to lay out a zone the table arranges, or asks for an order it holds no cards for."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class StalePosition(CardworkError):
    """Raised when a move is built on a position that later commits have superseded."""

    def __init__(self, base_seq: int, head: int) -> None:
        super().__init__(f"Move was built on sequence {base_seq} while the table stands at {head}")
        self.base_seq = base_seq
        self.head = head


class UndoUnavailable(CardworkError):
    """Raised when the transaction at the head of the journal is closed to undo."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
