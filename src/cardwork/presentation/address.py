from cardwork.zones.family import Family
from cardwork.zones.zone import ZoneId

type Address = Family | ZoneId


def at(address: Address, seat: int) -> ZoneId:
    """The zone an address names at one seat: a family's own zone there, or the zone of the table it names.

    A layout is built for one observer, so every zone it carries is concrete. This is where that happens: a
    family stands a zone at every seat and answers for the seat asked, and a zone of the table stands for
    itself, since the seats share it.

    Args:
        address: the family standing a zone at every seat, or the zone of the table.
        seat: the seat the zone is wanted for.
    """
    if isinstance(address, Family):
        return address.of(seat)

    return address


def word_of(address: Address) -> str:
    """The word a client names that zone or family by, which is the group an intent carries.

    A family is named by its own name and a zone of the table by its id, which are the words the rules read a
    group back against: `family_named` matches the first and a game's own constant the second.
    """
    if isinstance(address, Family):
        return address.name

    return address
