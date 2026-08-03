from typing import Self

from pydantic import model_validator

from cardwork.models.base import BaseFrozen
from cardwork.moves.actions import AnyAction, group_of
from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.zones.zone import ZoneId


class Gesture(BaseFrozen):
    """One kind of move as a player makes it: the zone the cards come out of, and the place clicked to send it.

    A move is matched to its gesture by `kind` and `group`, which together are the whole of what an intent
    says beside the positions it names. `group` names the group this gesture is for, and reads None where the
    group tells no two gestures of that kind apart — a kind carrying no group at all reads None here.

    `picked` is the zone the move's indices address, which is the zone a player selects cards in. It is a
    concrete zone because a layout is built for one observer, so the hand a move names is that observer's own.
    `target` is the zone clicked to commit, and reads None where the commit lands on a seat, since the move
    names the seat itself. `caption` states in words what the gesture does, for a player weighing it.
    """

    kind: ActionKind
    group: str | None
    picked: ZoneId
    commit: Commit
    target: ZoneId | None
    caption: str

    def matches(self, action: AnyAction) -> bool:
        """Whether a move carrying that action is the move this gesture makes.

        The kind and the group are the whole of what an intent states beside the positions it names, so those
        two settle it: a gesture stating a group stands for the moves naming that group, and a gesture stating
        none stands for every move of its kind. This is the rule an interface reads a served move through,
        and `Layout` holds a run of gestures to one answer for it.
        """
        return self.kind == action.kind and (self.group is None or self.group == group_of(action))

    @model_validator(mode="after")
    def _the_commit_names_what_it_lands_on(self) -> Self:
        """Confirm a zone commit names its zone and a seat commit leaves the seat to the move.

        Raises:
            ValueError: when a zone commit names no target, or a seat commit names one.
        """
        if self.commit is Commit.ZONE and self.target is None:
            raise ValueError(f"A {self.kind} gesture committing onto a zone names that zone, and names none")

        if self.commit is Commit.SEAT and self.target is not None:
            raise ValueError(
                f"A {self.kind} gesture committing onto a seat takes it from the move, and names zone {self.target!r}"
            )

        return self
