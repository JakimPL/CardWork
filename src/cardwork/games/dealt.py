from collections.abc import Mapping

from cardwork.exceptions import GameValidationError
from cardwork.positions.position import Position
from cardwork.states.state import StateT
from cardwork.zones.family import Family


def confirm_dealt(
    position: Position[StateT],
    family: Family,
    sizes: Mapping[int, int] | int,
) -> None:
    """Confirm each seat holds the count the deal owes it in its own zone of one family.

    A game reads the table its deal laid out through this, which states the count each seat is owed once and
    names the seats holding another.

    Args:
        position: the table as the deal left it.
        family: the zones the counts are read over, one standing at each seat.
        sizes: the count every seat is owed, or the count each seat is owed of its own.

    Raises:
        GameValidationError: when a seat holds a count other than the deal owes it.
        KeyError: when the sizes state a count per seat and name none for a seat in play.
    """
    owed = family.dealt(sizes, position.seats)
    short = tuple(seat for seat in position.seats if position.board.count(family.of(seat)) != owed[family.of(seat)])
    if short:
        raise GameValidationError(f"Seats {short} hold a {family.name} of a size other than the deal gives them")
