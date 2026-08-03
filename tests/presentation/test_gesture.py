from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.moves.kind import ActionKind
from cardwork.presentation.commit import Commit
from cardwork.presentation.gesture import Gesture
from cardwork.zones.zone import ZoneId

from ..cases import Case, descriptions
from .demo import PILE, hand_of

PICKED: Final[ZoneId] = hand_of(0)


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
