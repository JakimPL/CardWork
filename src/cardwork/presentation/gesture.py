from typing import Self

from pydantic import model_validator

from cardwork.models.base import BaseFrozen
from cardwork.moves.actions import AnyAction, group_of
from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.zones.zone import ZoneId


class Gesture(BaseFrozen):
    """One kind of move as a player makes it: the zone the cards come out of, and how the move is sent.

    A move is matched to its gesture by `kind` and `group`, which together are the whole of what an intent
    says beside the positions it names. `group` names the group this gesture is for, and reads None where the
    group tells no two gestures of that kind apart — a kind carrying no group at all reads None here.

    `picked` is the zone the move's indices address, which is the zone a player selects cards in. It is a
    concrete zone because a layout is built for one observer, so the hand a move names is that observer's own.
    It reads None for a move naming no card at all, which leaves a player nothing to select and an interface
    no zone to hold open: a pass is made in no zone, so it picks in none.

    `commit` is how the move leaves, and `target` the zone it lands on, which reads None for the two commits
    naming no zone — a seat commit takes its seat from the move, and a word is said rather than pointed at.
    `caption` states in words what the gesture does, for a player weighing it.
    """

    kind: ActionKind
    group: str | None
    picked: ZoneId | None
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
        """Confirm the commit and the target say the same thing about where the move lands.

        Raises:
            ValueError: when a zone commit names no target, or a commit landing on no zone of its own names one.
        """
        misnamed = self._misnamed()
        if misnamed is not None:
            raise ValueError(misnamed)

        return self

    def _misnamed(self) -> str | None:
        """What the place this gesture names gets wrong, and None where the commit and the target agree.

        Each commit is answered for in turn, so a member added to the vocabulary states here what it lands on.
        """
        match self.commit:
            case Commit.ZONE:
                if self.target is None:
                    return f"A {self.kind} gesture committing onto a zone names that zone, and names none"

                return None

            case Commit.SEAT:
                if self.target is not None:
                    return (
                        f"A {self.kind} gesture committing onto a seat takes it from the move, "
                        f"and names zone {self.target!r}"
                    )

                return None

            case Commit.WORD:
                if self.target is not None:
                    return f"A {self.kind} gesture said by its word lands on no zone, and names zone {self.target!r}"

                return None
