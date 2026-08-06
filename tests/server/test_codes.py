from dataclasses import dataclass
from typing import Final

import pytest

from cardserver.codes import (
    CODE_LENGTH,
    a_drawn_code,
    admits,
    ranks_in,
    spoken,
    written,
)
from cardwork.cards.orders import RANK_SEQUENCE
from cardwork.cards.rank import Rank, Ranks
from tests.cases import Case, descriptions

HAND: Final[Ranks] = (Rank.KING, Rank.TEN, Rank.ACE, Rank.JACK, Rank.TWO)


@dataclass(frozen=True)
class ReadingCase(Case):
    offered: str
    ranks: Ranks | None


READINGS: Final[tuple[ReadingCase, ...]] = (
    ReadingCase(
        description="a code written as it is drawn",
        offered="K10AJ2",
        ranks=HAND,
    ),
    ReadingCase(
        description="a code in lower case, which a person types either way",
        offered="k10aj2",
        ranks=HAND,
    ),
    ReadingCase(
        description="a code spoken apart, hyphenated and underscored at once",
        offered="K 10-A_J 2",
        ranks=HAND,
    ),
    ReadingCase(
        description="the ten taken before the one, which names no rank alone",
        offered="10",
        ranks=(Rank.TEN,),
    ),
    ReadingCase(
        description="two tens in a row, each read whole",
        offered="1010",
        ranks=(Rank.TEN, Rank.TEN),
    ),
    ReadingCase(
        description="every rank of the deck, the eight among them",
        offered="".join(RANK_SEQUENCE),
        ranks=RANK_SEQUENCE,
    ),
    ReadingCase(
        description="digits that read as no hand, since a leading zero names nothing",
        offered="012345",
        ranks=None,
    ),
    ReadingCase(
        description="a one standing alone",
        offered="1",
        ranks=None,
    ),
    ReadingCase(
        description="a zero standing alone",
        offered="0",
        ranks=None,
    ),
    ReadingCase(
        description="a ten with a one left over",
        offered="101",
        ranks=None,
    ),
    ReadingCase(
        description="a letter the deck holds no rank for",
        offered="KZA",
        ranks=None,
    ),
    ReadingCase(
        description="nothing offered at all",
        offered="",
        ranks=None,
    ),
    ReadingCase(
        description="nothing but the separators a code is written with",
        offered=" - ",
        ranks=None,
    ),
)


@pytest.mark.parametrize("case", READINGS, ids=descriptions(READINGS))
def test_a_code_reads_as_the_hand_of_ranks_it_names(case: ReadingCase) -> None:
    assert ranks_in(case.offered) == case.ranks


def test_a_drawn_code_is_a_hand_of_the_length_a_code_is() -> None:
    drawn = ranks_in(a_drawn_code())

    assert drawn is not None
    assert len(drawn) == CODE_LENGTH


def test_a_hand_is_written_as_the_code_it_reads_from() -> None:
    assert written(HAND) == "K10AJ2"
    assert ranks_in(written(HAND)) == HAND


def test_a_hand_is_spoken_one_rank_apart_from_the_next() -> None:
    assert spoken(HAND) == "K 10 A J 2"
    assert ranks_in(spoken(HAND)) == HAND


@dataclass(frozen=True)
class AdmissionCase(Case):
    code: str
    offered: str
    admitted: bool


ADMISSIONS: Final[tuple[AdmissionCase, ...]] = (
    AdmissionCase(
        description="the same hand written the same way",
        code="K10AJ2",
        offered="K10AJ2",
        admitted=True,
    ),
    AdmissionCase(
        description="the same hand written as a person passes it on",
        code="K10AJ2",
        offered="k 10-a j 2",
        admitted=True,
    ),
    AdmissionCase(
        description="another hand of the same length",
        code="K10AJ2",
        offered="K10AJ3",
        admitted=False,
    ),
    AdmissionCase(
        description="the hand as far as it goes, which is a code cut short",
        code="K10AJ2",
        offered="K10AJ",
        admitted=False,
    ),
    AdmissionCase(
        description="a ten written apart, which dropping the separators leaves whole",
        code="10",
        offered="1 0",
        admitted=True,
    ),
    AdmissionCase(
        description="something offered that reads as no hand at all",
        code="K10AJ2",
        offered="hello",
        admitted=False,
    ),
    AdmissionCase(
        description="nothing offered against a code that reads",
        code="K10AJ2",
        offered="",
        admitted=False,
    ),
    AdmissionCase(
        description="a code that reads as no hand, which admits nobody offering it",
        code="not-a-hand",
        offered="not-a-hand",
        admitted=False,
    ),
)


@pytest.mark.parametrize("case", ADMISSIONS, ids=descriptions(ADMISSIONS))
def test_a_code_admits_what_reads_as_the_same_hand(case: AdmissionCase) -> None:
    assert admits(case.code, case.offered) is case.admitted


def test_a_drawn_code_admits_itself() -> None:
    drawn = a_drawn_code()

    assert admits(drawn, drawn)
