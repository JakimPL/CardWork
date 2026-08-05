from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.exceptions import LogicError
from cardwork.rounds.state import BEFORE_THE_FIRST_ROUND, USUAL_AWARD, RoundState
from cardwork.states.award import Award
from cardwork.states.state import Points
from tests.cases import Case, descriptions

FRESH = "fresh"


def test_a_cursor_stands_before_the_first_round_until_one_opens() -> None:
    state = RoundState(phase=FRESH)

    assert state.round_number == BEFORE_THE_FIRST_ROUND
    assert state.leader is None
    assert state.round_points == ()
    assert state.points is None


def test_a_cursor_before_the_first_round_names_no_leading_seat() -> None:
    state = RoundState(phase=FRESH)

    with pytest.raises(LogicError, match="No round has opened"):
        state.led_by  # pylint: disable=pointless-statement


def test_a_cursor_of_an_open_round_names_the_seat_leading_it() -> None:
    state = RoundState(phase=FRESH, round_number=3, leader=2, round_points=(0, 4))

    assert state.led_by == 2
    assert state.round_number == 3


def test_a_cursor_is_won_at_the_end_of_the_standing_most_matches_are() -> None:
    assert RoundState(phase=FRESH).award == USUAL_AWARD
    assert USUAL_AWARD == Award.HIGHEST


@dataclass(frozen=True)
class EndingCase(Case):
    """One cursor beside a standing, and whether the clauses it carries call the match decided."""

    cursor: RoundState
    standing: Points
    decided: bool


ENDINGS: Final[tuple[EndingCase, ...]] = (
    EndingCase(
        description="a match of five rounds stands open at the fourth",
        cursor=RoundState(phase=FRESH, round_number=4, rounds=5),
        standing=(3, 1, 0),
        decided=False,
    ),
    EndingCase(
        description="a match of five rounds is decided once the fifth has been played",
        cursor=RoundState(phase=FRESH, round_number=5, rounds=5),
        standing=(3, 1, 0),
        decided=True,
    ),
    EndingCase(
        description="a match to a score stands open while every seat is short of it",
        cursor=RoundState(phase=FRESH, round_number=7, target=100),
        standing=(99, 40),
        decided=False,
    ),
    EndingCase(
        description="a match to a score is decided by the seat that reaches it",
        cursor=RoundState(phase=FRESH, round_number=7, target=100),
        standing=(100, 40),
        decided=True,
    ),
    EndingCase(
        description="a match to a score is decided by whoever reaches it, the fewest winning it or not",
        cursor=RoundState(phase=FRESH, round_number=7, target=100, award=Award.LOWEST),
        standing=(100, 40),
        decided=True,
    ),
    EndingCase(
        description="a match to a lead stands open while the two best seats are level",
        cursor=RoundState(phase=FRESH, round_number=3, lead=2),
        standing=(4, 4, 1),
        decided=False,
    ),
    EndingCase(
        description="a match to a lead is decided once the best seat pulls that far clear",
        cursor=RoundState(phase=FRESH, round_number=3, lead=2),
        standing=(6, 4, 1),
        decided=True,
    ),
    EndingCase(
        description="a match to a lead won by the fewest reads the standing from its own end",
        cursor=RoundState(phase=FRESH, round_number=3, lead=2, award=Award.LOWEST),
        standing=(1, 3, 6),
        decided=True,
    ),
    EndingCase(
        description="a lead at the highest end says nothing about a match won at the lowest",
        cursor=RoundState(phase=FRESH, round_number=3, lead=2, award=Award.LOWEST),
        standing=(1, 2, 6),
        decided=False,
    ),
    EndingCase(
        description="a match of several clauses is decided by the first of them met",
        cursor=RoundState(phase=FRESH, round_number=2, rounds=10, target=8),
        standing=(8, 1),
        decided=True,
    ),
    EndingCase(
        description="a match whose game states its own ending is left to play on",
        cursor=RoundState(phase=FRESH, round_number=40),
        standing=(30, 12),
        decided=False,
    ),
)


@pytest.mark.parametrize("case", ENDINGS, ids=descriptions(ENDINGS))
def test_a_cursor_reads_the_clauses_its_match_ends_on_against_the_standing(case: EndingCase) -> None:
    assert case.cursor.concluded(case.standing) is case.decided
