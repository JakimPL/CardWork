from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    """One row of a behaviour table, named by what it demonstrates.

    A case states the whole of what its behaviour produces rather than the single value under test, so the
    run of cases reads as the rule it encodes and a failure names the expectation that broke.
    """

    description: str


def descriptions(cases: Sequence[Case]) -> list[str]:
    """The names of the cases, which a parametrized test takes as its ids."""
    return [case.description for case in cases]
