from collections.abc import Iterable
from typing import Annotated

from pydantic import BeforeValidator


def _as_seats(value: object) -> object:
    """The seats a turn is stated as, gathered into the collection a set of seats is validated from.

    A game states the turn the way its rules read it: one seat leads, a rotation owes a commitment at once, a
    tally of seats is already a set. A single seat arrives as the number it is and stands for the turn holding
    it alone, and a run of seats arrives as any iterable, so `to_act=leader` and `to_act=range(players)` both
    reach the field as the seats they name. Anything else passes through for the field to validate and refuse.
    """
    if isinstance(value, int):
        return (value,)

    if isinstance(value, Iterable):
        return tuple(value)

    return value


type Seats = Annotated[frozenset[int], BeforeValidator(_as_seats)]
