from typing import Final

import pytest

from cardwork.exceptions import LogicError
from cardwork.models.held import held

A_SEAT: Final[int] = 0
NOTHING_AT_ALL: Final[int] = 0


def test_a_value_standing_there_is_read_back_as_it_is() -> None:
    assert held(A_SEAT, "seat leads the round") == A_SEAT


def test_a_value_that_reads_as_nothing_still_stands_there() -> None:
    assert held(NOTHING_AT_ALL, "seat leads the round") == NOTHING_AT_ALL
    assert held((), "cards lie on the table") == ()


def test_nothing_standing_there_is_refused_naming_what_is_missing() -> None:
    with pytest.raises(LogicError, match="No round has opened, so no seat leads one"):
        held(None, "round has opened, so no seat leads one")
