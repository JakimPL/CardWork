from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardserver.limits import NAME_LONGEST
from cardserver.oversight import Posting
from cardserver.schemas import Founding
from tests.cases import Case, descriptions

from ..games.demo import SEATS
from .company import a_sealed_round

A_HOST: Final[str] = "Ada"
A_PLAIN_NAME: Final[str] = "green-baize"
SPACED: Final[str] = "  green-baize  "


@dataclass(frozen=True)
class Naming(Case):
    """One name a table might be asked to gather under, and whether a door lets it through."""

    offered: str


THROUGH_A_DIRECTORY: Final[tuple[Naming, ...]] = (
    Naming(description="a name climbing out of wherever it is written", offered="../../escape"),
    Naming(description="a name reading from the root of the machine", offered="/tmp/pwned"),
    Naming(description="a name reading through a Windows directory", offered="a\\b"),
    Naming(description="a name that is one step up and nothing else", offered=".."),
    Naming(description="a name that is where it already stands", offered="."),
    Naming(description="a name holding nothing but space", offered="   "),
    Naming(description="a name holding a character that shows nothing", offered="green\nbaize"),
    Naming(description="a name wider than a name is read at", offered="A" * (NAME_LONGEST + 1)),
)


@pytest.mark.parametrize("case", THROUGH_A_DIRECTORY, ids=descriptions(THROUGH_A_DIRECTORY))
def test_a_name_no_table_is_read_by_is_refused_of_a_company_founding_one(case: Naming) -> None:
    """The door a self-serve lobby opens through, which is where a name a guest chose arrives."""
    with pytest.raises(ValidationError):
        Founding(table=case.offered, name=A_HOST, choice=a_sealed_round(SEATS))


@pytest.mark.parametrize("case", THROUGH_A_DIRECTORY, ids=descriptions(THROUGH_A_DIRECTORY))
def test_a_name_no_table_is_read_by_is_refused_of_an_overseer_posting_one(case: Naming) -> None:
    """The other door, which the panel gathers through and which is held to the same rule."""
    with pytest.raises(ValidationError):
        Posting(table=case.offered, choice=a_sealed_round(SEATS))


def test_a_name_a_table_reads_at_is_taken_with_the_space_around_it_trimmed() -> None:
    """What a person types is what they meant, so the space they typed around it is no part of the name."""
    assert Founding(table=SPACED, name=A_HOST, choice=a_sealed_round(SEATS)).table == A_PLAIN_NAME


def test_a_name_that_reads_at_a_table_is_admitted_at_every_door() -> None:
    assert Founding(table=A_PLAIN_NAME, name=A_HOST, choice=a_sealed_round(SEATS)).table == A_PLAIN_NAME
    assert Posting(table=A_PLAIN_NAME, choice=a_sealed_round(SEATS)).table == A_PLAIN_NAME
