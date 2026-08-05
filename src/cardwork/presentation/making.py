from typing import Self

from pydantic import model_validator

from cardwork.models.base import BaseFrozen
from cardwork.moves.kind import ActionKind
from cardwork.presentation.address import Address, at, word_of
from cardwork.presentation.commit import Commit
from cardwork.presentation.gesture import Gesture, Matching, misnamed


class Making(BaseFrozen):
    """One kind of move as any seat makes it: where its cards are picked, and how it is sent.

    A `Gesture` is this same statement with a seat bound to it, which is what the layout of one observer
    carries. The difference is the addressing: a making names the family a zone belongs to where a gesture names
    the zone that family stands at one seat, so a game states a move once and every seat is offered its own.

    `group`, `picked` and `target` each name a zone of the table or a family standing one at every seat. A group
    travels as the word it stands for, since that is what an intent carries: a family under its name, a zone of
    the table under its id. A game whose group names neither states the word itself.
    """

    kind: ActionKind
    group: Address | None
    picked: Address | None
    commit: Commit
    target: Address | None
    caption: str

    @property
    def matching(self) -> Matching:
        """The kind and the group word a move is matched to this by, which stand the same at every seat."""
        return self.kind, None if self.group is None else word_of(self.group)

    def gesture(self, seat: int) -> Gesture:
        """This move as one seat makes it, every zone it names concrete for that seat.

        Args:
            seat: the seat making the move, which is the observer the layout is built for.
        """
        return Gesture(
            kind=self.kind,
            group=None if self.group is None else word_of(self.group),
            picked=None if self.picked is None else at(self.picked, seat),
            commit=self.commit,
            target=None if self.target is None else at(self.target, seat),
            caption=self.caption,
        )

    @model_validator(mode="after")
    def _the_commit_names_what_it_lands_on(self) -> Self:
        """Confirm the commit and the target say the same thing about where the move lands.

        Raises:
            ValueError: when a zone commit names no target, or a commit landing on no zone of its own names one.
        """
        refusal = misnamed(self.kind, self.commit, None if self.target is None else word_of(self.target))
        if refusal is not None:
            raise ValueError(refusal)

        return self
