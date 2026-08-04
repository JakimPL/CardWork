from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.moves.actions import AnyAction, Give, Take
from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.presentation.gesture import Gesture
from cardwork.zones.zone import ZoneId
from tests.cases import Case, descriptions

from .demo import PILE, STACK, hand_of

PICKED: Final[ZoneId] = hand_of(0)
GIVEN_UP: Final[frozenset[int]] = frozenset({0})
NEXT_SEAT: Final[int] = 1


@dataclass(frozen=True)
class RefusalCase(Case):
    commit: Commit
    target: ZoneId | None
    refusal: str


REFUSALS: Final[tuple[RefusalCase, ...]] = (
    RefusalCase(
        description="a commit onto a zone naming none",
        commit=Commit.ZONE,
        target=None,
        refusal="committing onto a zone names that zone",
    ),
    RefusalCase(
        description="a commit onto a seat naming a zone besides",
        commit=Commit.SEAT,
        target=PILE,
        refusal="committing onto a seat takes it from the move",
    ),
)


@pytest.mark.parametrize("case", REFUSALS, ids=descriptions(REFUSALS))
def test_a_gesture_names_the_place_its_commit_lands_on_and_no_other(case: RefusalCase) -> None:
    with pytest.raises(ValidationError, match=case.refusal):
        Gesture(
            kind=ActionKind.TAKE,
            group=PILE,
            picked=PICKED,
            commit=case.commit,
            target=case.target,
            caption="Exchange with the pile",
        )


def test_a_gesture_committing_onto_a_zone_holds_the_zone_it_names() -> None:
    gesture = Gesture(
        kind=ActionKind.TAKE,
        group=PILE,
        picked=PICKED,
        commit=Commit.ZONE,
        target=PILE,
        caption="Exchange with the pile",
    )

    assert gesture.target == PILE


def test_a_gesture_committing_onto_a_seat_leaves_the_seat_to_the_move() -> None:
    gesture = Gesture(
        kind=ActionKind.GIVE,
        group=None,
        picked=PICKED,
        commit=Commit.SEAT,
        target=None,
        caption="Pass to the next seat",
    )

    assert gesture.target is None


def a_gesture(kind: ActionKind, group: str | None) -> Gesture:
    """A gesture of that kind and group, the rest of it standing where it has no bearing on a match."""
    return Gesture(
        kind=kind,
        group=group,
        picked=PICKED,
        commit=Commit.ZONE,
        target=PILE,
        caption="Exchange with the pile",
    )


@dataclass(frozen=True)
class MatchCase(Case):
    kind: ActionKind
    group: str | None
    action: AnyAction
    matched: bool


MATCHES: Final[tuple[MatchCase, ...]] = (
    MatchCase(
        description="a move naming the kind and the group the gesture states",
        kind=ActionKind.TAKE,
        group=PILE,
        action=Take(group=PILE, indices=GIVEN_UP),
        matched=True,
    ),
    MatchCase(
        description="a move naming another group of that kind",
        kind=ActionKind.TAKE,
        group=STACK,
        action=Take(group=PILE, indices=GIVEN_UP),
        matched=False,
    ),
    MatchCase(
        description="a move of another kind naming that group",
        kind=ActionKind.PLAY,
        group=PILE,
        action=Take(group=PILE, indices=GIVEN_UP),
        matched=False,
    ),
    MatchCase(
        description="a gesture standing for every group of its kind",
        kind=ActionKind.TAKE,
        group=None,
        action=Take(group=PILE, indices=GIVEN_UP),
        matched=True,
    ),
    MatchCase(
        description="a move of a kind carrying no group",
        kind=ActionKind.GIVE,
        group=None,
        action=Give(target_player=NEXT_SEAT, indices=GIVEN_UP),
        matched=True,
    ),
    MatchCase(
        description="a gesture naming a group where the move carries none",
        kind=ActionKind.GIVE,
        group=PILE,
        action=Give(target_player=NEXT_SEAT, indices=GIVEN_UP),
        matched=False,
    ),
)


@pytest.mark.parametrize("case", MATCHES, ids=descriptions(MATCHES))
def test_a_move_is_made_by_the_gesture_of_its_kind_and_group(case: MatchCase) -> None:
    assert a_gesture(case.kind, case.group).matches(case.action) is case.matched
