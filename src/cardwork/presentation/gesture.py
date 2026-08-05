from typing import Self

from pydantic import model_validator

from cardwork.models.base import BaseFrozen
from cardwork.moves.actions import AnyAction, group_of
from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.presentation.repeats import repeated
from cardwork.zones.zone import ZoneId

type Matching = tuple[ActionKind, str | None]


def misnamed(
    kind: ActionKind,
    commit: Commit,
    target: str | None,
) -> str | None:
    """What the place a move names gets wrong, and None where the commit and the target agree.

    Each commit is answered for in turn, so a member added to the vocabulary states here what it lands on. A
    `Gesture` and the `Making` it is bound from are held to this one rule, so a move refused at a table is
    refused as the game states it.

    Args:
        kind: the kind of move, which the refusal names.
        commit: how the move is sent.
        target: the word for the place it lands on, and None where it names none.
    """
    match commit:
        case Commit.ZONE:
            if target is None:
                return f"A {kind} gesture committing onto a zone names that zone, and names none"

            return None

        case Commit.SEAT:
            if target is not None:
                return f"A {kind} gesture committing onto a seat takes it from the move, and names zone {target!r}"

            return None

        case Commit.WORD:
            if target is not None:
                return f"A {kind} gesture said by its word lands on no zone, and names zone {target!r}"

            return None


def mismatched(matchings: tuple[Matching, ...]) -> str | None:
    """What a run of gestures gets wrong about the moves it answers, and None where every move reaches one.

    A move is matched by its kind and the group it names, so a run answers each move once when no two of its
    gestures are matched alike and a gesture standing for every group of a kind stands alone. A `Layout` and the
    `Scene` it is drawn from are held to this one rule, so a run refused at a table is refused as a game states it.

    Args:
        matchings: the kind and group word of every gesture of the run, in the order the run states them.
    """
    twice = repeated(matchings)
    if twice:
        return f"A move matches one gesture, and these kinds and groups are stated twice: {twice}"

    overlapping = tuple(kind for kind in ActionKind if _groups_overlap(matchings, kind))
    if overlapping:
        return f"A gesture over every group of a kind stands alone, and these do not: {overlapping}"

    return None


def _groups_overlap(matchings: tuple[Matching, ...], kind: ActionKind) -> bool:
    """Whether one gesture of that kind stands for every group while another stands for one."""
    groups = tuple(group for matched, group in matchings if matched == kind)
    return None in groups and len(groups) > 1


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
        refusal = misnamed(self.kind, self.commit, self.target)
        if refusal is not None:
            raise ValueError(refusal)

        return self
