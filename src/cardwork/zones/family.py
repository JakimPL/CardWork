from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Final

from pydantic import Field, field_validator

from cardwork.exceptions import IllegalMove
from cardwork.models.base import BaseFrozen
from cardwork.zones.visibility import Visibility
from cardwork.zones.zone import Zone, ZoneId, Zones

SEPARATOR: Final[str] = ":"

type PerSeat = Callable[[int, int], Visibility]


class Family(BaseFrozen):
    """The zones one name gives every seat, under one word on arrangement and the sight each seat is owed.

    A hand, a blind dealt face down and a tray a seat commits into are each one family: the same kind of zone
    standing at every seat, told apart by the seat it belongs to. A game declares the family once and reads a
    seat's own zone out of it, which is what leaves the naming convention stated in one place:

        HANDS.of(2) == "hand:2"
        HANDS.zones(players=3)                       # the hand of every seat, filed under its own id
        HANDS.dealt(5, rotation(leader, players))     # five to each seat, from the leader onwards

    `visibility` is one policy for the whole family, or a policy read per seat where a family owes each seat a
    sight of its own: the board of one seat that every other seat reads is stated that way, the seat and the
    count of seats being what such a reading stands on.
    """

    name: str = Field(min_length=1)
    ordered: bool
    visibility: Visibility | PerSeat

    @field_validator("name")
    @classmethod
    def _name_leaves_the_seat_its_own_place(cls, name: str) -> str:
        if SEPARATOR in name:
            raise ValueError(f"A family is named apart from the seat it stands at, and {name!r} holds {SEPARATOR!r}")

        return name

    def of(self, seat: int) -> ZoneId:
        """The zone id this family gives one seat, which is what the rules read against."""
        return f"{self.name}{SEPARATOR}{seat}"

    def owns(self, zone_id: ZoneId) -> bool:
        """Whether a zone id names one of this family's zones."""
        name, separator, seat = zone_id.partition(SEPARATOR)
        return bool(separator) and name == self.name and seat.isdigit()

    def zones(self, players: int) -> Zones:
        """The zone this family stands at every seat of the table, each filed under the id it is named by."""
        seated = (self._zone(seat, players) for seat in range(players))
        return {zone.id: zone for zone in seated}

    def dealt(self, sizes: Mapping[int, int] | int, seats: Iterable[int]) -> Mapping[ZoneId, int]:
        """How many cards this family owes each of the named seats, in the order the seats are named.

        One size stands for every seat, and a size for each seat states a deal that varies: a seat on lead
        dealt a card more, or two families dealt at sizes of their own. The run the seats are named in is the
        run the cards are handed out in, so a game deals round the table from its leader by naming the seats in
        that order.

        Args:
            sizes: the count every seat is owed, or the count each seat is owed on its own.
            seats: the seats dealt to, in the order the deal reaches them.

        Raises:
            KeyError: when the sizes state a count per seat and the deal reaches a seat they name none for.
        """
        if isinstance(sizes, int):
            return {self.of(seat): sizes for seat in seats}

        return {self.of(seat): sizes[seat] for seat in seats}

    def _zone(self, seat: int, players: int) -> Zone:
        """The zone this family gives one seat, under the sight that seat is owed at a table of this size."""
        return Zone(
            id=self.of(seat),
            owner=seat,
            visibility=self._sight(seat, players),
            ordered=self.ordered,
        )

    def _sight(self, seat: int, players: int) -> Visibility:
        """The policy one seat's zone of this family lies under, read per seat where the family states it so."""
        if isinstance(self.visibility, Visibility):
            return self.visibility

        return self.visibility(seat, players)


def family_named(families: Iterable[Family], name: str, seat: int) -> Family:
    """The family one word names, out of the families a seat holds cards in.

    A client states the group its move comes out of by name, and this reads that word back to the family it
    stands for, which leaves the words a game is played with stated once and answered in one sentence.

    Raises:
        IllegalMove: when the word names none of the families given.
    """
    known = tuple(families)
    for family in known:
        if family.name == name:
            return family

    words = " or ".join(repr(family.name) for family in known)
    raise IllegalMove(f"Seat {seat} holds cards in {words}, and named {name!r}")
