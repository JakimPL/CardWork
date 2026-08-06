from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.moves.actions import Give, Play
from cardwork.moves.move import Move, Moves
from cardwork.views.projection import project_moves
from tests.cases import Case, descriptions

BY_ZERO: Final[Move] = Move(player=0, action=Play(group="table", indices=frozenset({0})))
ALSO_BY_ZERO: Final[Move] = Move(player=0, action=Play(group="table", indices=frozenset({1})))
BY_ONE: Final[Move] = Move(player=1, action=Give(target_player=2, indices=frozenset({0})))
BY_TWO: Final[Move] = Move(player=2, action=Play(group="meld", indices=frozenset({0, 1})))

OFFERED: Final[Moves] = (BY_ZERO, BY_ONE, ALSO_BY_ZERO, BY_TWO)
UNSEATED: Final[int] = 3


@dataclass(frozen=True)
class ObserverCase(Case):
    observer: int | None
    expected: Moves


OBSERVER_CASES: Final[tuple[ObserverCase, ...]] = (
    ObserverCase(
        description="a seat holding several reads them in the order the rules offered them",
        observer=0,
        expected=(BY_ZERO, ALSO_BY_ZERO),
    ),
    ObserverCase(
        description="a seat holding one reads that one",
        observer=1,
        expected=(BY_ONE,),
    ),
    ObserverCase(
        description="a spectator reads none, since a move belongs to a seat",
        observer=None,
        expected=(),
    ),
    ObserverCase(
        description="a seat the rules offered nothing reads none",
        observer=UNSEATED,
        expected=(),
    ),
)


@pytest.mark.parametrize("case", OBSERVER_CASES, ids=descriptions(OBSERVER_CASES))
def test_project_moves_narrows_the_run_to_the_moves_of_one_seat(case: ObserverCase) -> None:
    assert project_moves(OFFERED, case.observer) == case.expected


def test_project_moves_narrows_an_empty_run_to_an_empty_run() -> None:
    assert project_moves((), 0) == ()
