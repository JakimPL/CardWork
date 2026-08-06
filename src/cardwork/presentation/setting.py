from typing import Self

from pydantic import model_validator

from cardwork.models.base import BaseFrozen
from cardwork.presentation.lay import Lay
from cardwork.presentation.slot import Slot
from cardwork.presentation.spread import Spread
from cardwork.presentation.tally import Tally
from cardwork.zones.family import Family


class Setting(BaseFrozen):
    """One zone family laid out: how its owner reads it, how the table reads it, and what its count is called.

    A family stands the same zone at every seat, so a game states the arrangement once and every seat of the
    table is laid out from it. `held` is the lay the seat holding the zone reads, `seen` the lay the rest of the
    table reads, and `tally` the word its count reads under on a plaque.

    Each of the three is a way the zone reaches a player, and a setting states at least one of them: a family
    with no `seen` is one the table draws nowhere, a family with no `held` is one its owner reads no more of
    than anybody else, and a family carrying a tally alone is a holding kept off the table and counted on the
    plaques.
    """

    family: Family
    held: Lay | None
    seen: Lay | None
    tally: str | None

    def held_at(self, seat: int, place: int) -> Slot | None:
        """This family's zone at one seat as that seat reads it.

        Args:
            seat: the seat holding the zone, which is the observer the layout is built for.
            place: where it stands among the zones of that seat.

        Returns:
            The slot its owner reads it through, and None for a family its owner reads no zone of.
        """
        if self.held is None:
            return None

        return self.held.slot(self.family.of(seat), seat=seat, place=place)

    def seen_at(self, seat: int, place: int) -> Slot | None:
        """This family's zone at one seat as the rest of the table reads it.

        Args:
            seat: the seat holding the zone, which every other observer reads it at.
            place: where it stands among the zones of that seat.

        Returns:
            The slot the table reads it through, and None for a family the table draws nowhere.
        """
        if self.seen is None:
            return None

        return self.seen.slot(self.family.of(seat), seat=seat, place=place)

    def counted_at(self, seat: int) -> Tally | None:
        """What this family says for its size on the plaque of one seat.

        Returns:
            The tally the plaque carries, and None for a family whose size the plaque leaves out.
        """
        if self.tally is None:
            return None

        return Tally(zone=self.family.of(seat), label=self.tally)

    @model_validator(mode="after")
    def _the_setting_reaches_a_player(self) -> Self:
        """Confirm the family reaches a player: drawn at the seat holding it, drawn across the table, or counted.

        Raises:
            ValueError: when a family states no lay and no tally, which lays out nothing at all.
        """
        if self.held is None and self.seen is None and self.tally is None:
            raise ValueError(f"A zone reaches a player laid out or counted, and {self.family.name!r} does neither")

        return self

    @classmethod
    def hand(cls, family: Family, label: str, *, mine: str, tally: str) -> Self:
        """A holding its owner picks from, overlapped so every card of it stays legible.

        A hand shows its cards in place of a count at the seat holding it, since a seat reading its own holding
        counts it by looking, and carries the size of it across the table, since how many cards a seat holds is
        the whole of what its hand tells everybody else.

        Args:
            family: the hand standing at every seat.
            label: the word the table calls it by.
            mine: the word the seat holding it calls its own by.
            tally: the word its count reads under on a plaque.
        """
        return cls(
            family=family,
            held=Lay(label=mine, spread=Spread.FAN, counted=False),
            seen=Lay(label=label, spread=Spread.FAN, counted=True),
            tally=tally,
        )

    @classmethod
    def sealed(cls, family: Family, label: str) -> Self:
        """A single place a card is committed into, which reads the same way at every seat of the table.

        One place holds one card or stands empty, so the drawing says how much lies there and the whole table
        reads it alike: what a tray tells the players is whether the seat holding it has committed.
        """
        place = Lay(label=label, spread=Spread.SLOT, counted=False)
        return cls(family=family, held=place, seen=place, tally=label)
