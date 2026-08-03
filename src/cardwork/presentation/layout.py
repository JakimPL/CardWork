from collections import Counter
from collections.abc import Hashable, Mapping
from typing import Self

from pydantic import Field, model_validator

from cardwork.models.base import BaseFrozen
from cardwork.moves.kind import ActionKind
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.plaque import Plaque
from cardwork.presentation.readout import Readout
from cardwork.presentation.slot import Slot
from cardwork.zones.zone import ZoneId


def distinct[ValueT: Hashable](
    values: tuple[ValueT, ...],
) -> tuple[ValueT, ...]:
    """The values, each named a single time, in the order they first appear."""
    return tuple(dict.fromkeys(values))


def repeated[ValueT: Hashable](
    values: tuple[ValueT, ...],
) -> tuple[ValueT, ...]:
    """The values appearing more than once, each named a single time, in the order they first appear."""
    counts = Counter(values)
    return tuple(value for value in distinct(values) if counts[value] > 1)


class Layout(BaseFrozen):
    """Everything an interface needs to lay a game out for one seat, and nothing about how it looks.

    A game states one of these per observer, so every zone id, seat and gesture in it is concrete and the
    interface resolves nothing: it draws the slots where they belong, matches the moves it is served to the
    gestures, reads the cursor through the readouts and captions the phase from `phases`. What is left over —
    the size of a card, the colour of a highlight, the moment a heap collapses — is the interface's own.

    Every claim a layout makes about itself is checked as it is built, which leaves an interface free to trust
    it: one slot per zone, one slot per place in a region, one plaque per seat, one gesture per move, and every
    zone a gesture picks from or commits onto laid out as a slot the player can reach.
    """

    title: str
    observer: int | None
    players: int = Field(ge=1)
    slots: tuple[Slot, ...]
    gestures: tuple[Gesture, ...]
    plaques: tuple[Plaque, ...]
    readouts: tuple[Readout, ...]
    phases: Mapping[str, str]

    @model_validator(mode="after")
    def _the_observer_takes_a_seat(self) -> Self:
        """Confirm the observer is one of the seats, or a spectator holding none.

        Raises:
            ValueError: when the observer names a seat the table does not hold.
        """
        if self.observer is not None and not 0 <= self.observer < self.players:
            raise ValueError(f"Seat {self.observer} stands outside the {self.players} seats of the table")

        return self

    @model_validator(mode="after")
    def _every_zone_takes_one_slot(self) -> Self:
        """Confirm no zone is laid out twice, since a card lies in one place.

        Raises:
            ValueError: when two slots name the same zone.
        """
        twice = repeated(tuple(slot.zone for slot in self.slots))
        if twice:
            raise ValueError(f"A zone is laid out once, and these take two slots apiece: {twice}")

        return self

    @model_validator(mode="after")
    def _every_place_holds_one_slot(self) -> Self:
        """Confirm the slots of a region fall in a settled order.

        Raises:
            ValueError: when two slots of one region take the same place.
        """
        twice = repeated(tuple((slot.region, slot.place) for slot in self.slots))
        if twice:
            raise ValueError(f"A place in a region holds one slot, and these hold two apiece: {twice}")

        return self

    @model_validator(mode="after")
    def _every_seat_takes_one_plaque(self) -> Self:
        """Confirm the plaques read across the whole table, one to a seat.

        Raises:
            ValueError: when the plaques name other than each seat of the table exactly once.
        """
        seated = tuple(plaque.seat for plaque in self.plaques)
        if sorted(seated) != list(range(self.players)):
            raise ValueError(f"Each of the {self.players} seats takes one plaque, and these are named: {seated}")

        return self

    @model_validator(mode="after")
    def _every_move_matches_one_gesture(self) -> Self:
        """Confirm the kind and group of a move reach a single gesture.

        Raises:
            ValueError: when two gestures share a kind and a group, or when a gesture matching every group of
                one kind stands beside another gesture of that kind.
        """
        twice = repeated(tuple((gesture.kind, gesture.group) for gesture in self.gestures))
        if twice:
            raise ValueError(f"A move matches one gesture, and these kinds and groups are stated twice: {twice}")

        overlapping = tuple(kind for kind in ActionKind if self._groups_overlap(kind))
        if overlapping:
            raise ValueError(f"A gesture over every group of a kind stands alone, and these do not: {overlapping}")

        return self

    @model_validator(mode="after")
    def _every_gesture_reaches_its_zones(self) -> Self:
        """Confirm a player can point at the cards a gesture picks and the zone it commits onto.

        Raises:
            ValueError: when a gesture picks from or commits onto a zone no slot lays out.
        """
        laid = {slot.zone for slot in self.slots}
        self._laid_out(tuple(gesture.picked for gesture in self.gestures), laid, "picked from")
        self._laid_out(
            tuple(gesture.target for gesture in self.gestures if gesture.target is not None),
            laid,
            "committed onto",
        )
        return self

    @model_validator(mode="after")
    def _every_field_reads_once(self) -> Self:
        """Confirm no field of the cursor is shown twice.

        Raises:
            ValueError: when two readouts name the same field.
        """
        twice = repeated(tuple(readout.field for readout in self.readouts))
        if twice:
            raise ValueError(f"A field of the cursor reads once, and these take two readouts apiece: {twice}")

        return self

    def _groups_overlap(self, kind: ActionKind) -> bool:
        """Whether one gesture of that kind stands for every group while another stands for one."""
        groups = tuple(gesture.group for gesture in self.gestures if gesture.kind == kind)
        return None in groups and len(groups) > 1

    @staticmethod
    def _laid_out(named: tuple[ZoneId, ...], laid: set[ZoneId], reached: str) -> None:
        """Confirm every zone a gesture names is one the slots lay out.

        Raises:
            ValueError: when a named zone takes no slot.
        """
        missing = distinct(tuple(zone for zone in named if zone not in laid))
        if missing:
            raise ValueError(f"A zone {reached} takes a slot of its own, and these take none: {missing}")
