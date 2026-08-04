from typing import Final

from cardwork.exceptions import IllegalMove
from cardwork.moves.actions import AnyAction, kind_of
from cardwork.moves.kind import ActionKind
from cardwork.moves.move import Move

ONE_INTENT: Final[int] = 1


class Intents[ActionT: AnyAction]:
    """The intents a game is played with: the vocabulary a move is read against, and the type it reads back as.

    A game states the actions its rules answer to, and the engine holds every move to them: a move carrying
    one of them reads back as that action, and a move carrying another is refused ahead of the rules that
    would read it. So a game states its vocabulary once, in the one place a reader looks for it, and each of
    its rules methods is about the moves it plays.

    The declaration is generic in the actions it names, which is what carries the vocabulary into the types a
    game is written in: `read` answers with the actions the game stated, and a `match` over that answer is
    covered by their cases alone.

        intents: ClassVar[Intents[Take | Give]] = Intents(Take, Give)

    A game states no vocabulary by leaving `Game.intents` at None, which states a condition on nothing: every
    intent of `AnyAction` reaches such a game's rules, whatever the vocabulary grows to hold. Naming an empty
    run of actions is a different thing and a refusal, since it leaves a game no move to be played with.
    """

    def __init__(self, *accepted: type[ActionT]) -> None:
        """The actions a game reads, in the order it names them.

        Raises:
            ValueError: when no action is named, which leaves a game no move to be played with.
        """
        if not accepted:
            raise ValueError("A game is played with one intent at the least, and none were named")

        self._accepted: tuple[type[ActionT], ...] = accepted

    @property
    def accepted(self) -> tuple[type[ActionT], ...]:
        """The actions this vocabulary holds, in the order the game named them."""
        return self._accepted

    @property
    def kinds(self) -> tuple[ActionKind, ...]:
        """The words those actions carry, which is what a client sends one of."""
        return tuple(kind_of(action) for action in self._accepted)

    def read(self, move: Move) -> ActionT:
        """The intent behind a move, as one of the actions this game is played with.

        Raises:
            IllegalMove: when the move carries an intent the vocabulary leaves out.
        """
        for accepted in self._accepted:
            if isinstance(move.action, accepted):
                return move.action

        raise IllegalMove(f"Seat {move.player} makes {self._spoken()}, and offered a {move.action.kind}")

    def _spoken(self) -> str:
        """The words of this vocabulary as a phrase, which is how a refusal states what a game is played with."""
        spoken = tuple(f"a {kind}" for kind in self.kinds)
        if len(spoken) == ONE_INTENT:
            return spoken[0]

        return f"{', '.join(spoken[:-1])} or {spoken[-1]}"
