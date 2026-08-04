from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.rounds.conclusion import Conclusion
from cardwork.rounds.state import RoundState
from tests.cases import Case, descriptions

ROUNDS: Final[int] = 5
TARGET: Final[int] = 100
LEAD: Final[int] = 2
BELOW_THE_LEAST: Final[int] = 0


@dataclass(frozen=True)
class ClauseCase(Case):
    """One conclusion beside every clause it states, which is the whole of how long its match runs."""

    conclusion: Conclusion
    rounds: int | None
    target: int | None
    lead: int | None


CLAUSES: Final[tuple[ClauseCase, ...]] = (
    ClauseCase(
        description="a match of a count of rounds",
        conclusion=Conclusion(rounds=ROUNDS),
        rounds=ROUNDS,
        target=None,
        lead=None,
    ),
    ClauseCase(
        description="a match to a score some seat reaches",
        conclusion=Conclusion(target=TARGET),
        rounds=None,
        target=TARGET,
        lead=None,
    ),
    ClauseCase(
        description="a match to a lead held over the next best",
        conclusion=Conclusion(lead=LEAD),
        rounds=None,
        target=None,
        lead=LEAD,
    ),
    ClauseCase(
        description="a match to a score or a count of rounds, whichever arrives first",
        conclusion=Conclusion(rounds=ROUNDS, target=TARGET),
        rounds=ROUNDS,
        target=TARGET,
        lead=None,
    ),
)


@pytest.mark.parametrize("case", CLAUSES, ids=descriptions(CLAUSES))
def test_a_conclusion_states_the_clauses_it_was_given(case: ClauseCase) -> None:
    assert case.conclusion.rounds == case.rounds
    assert case.conclusion.target == case.target
    assert case.conclusion.lead == case.lead


def test_a_match_stating_no_clause_at_all_is_refused() -> None:
    with pytest.raises(ValidationError, match="states at least one"):
        Conclusion()


@pytest.mark.parametrize("clause", ["rounds", "target", "lead"])
def test_a_clause_below_the_least_a_match_runs_to_is_refused(clause: str) -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        Conclusion(**{clause: BELOW_THE_LEAST})


def test_every_clause_a_conclusion_states_is_a_field_the_cursor_carries() -> None:
    """The clauses are stamped onto the cursor by name, so the two vocabularies stand or fall together."""
    assert set(Conclusion.model_fields) <= set(RoundState.model_fields)
