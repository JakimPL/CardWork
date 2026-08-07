from collections.abc import Mapping
from typing import Self

from pydantic import Field, model_validator

from cardwork.models.base import BaseFrozen
from cardwork.presentation.gesture import Gesture, mismatched
from cardwork.presentation.interlude import Interlude, uncaptioned
from cardwork.presentation.plaque import Plaque
from cardwork.presentation.readout import Readout, misread
from cardwork.presentation.repeats import distinct, repeated
from cardwork.presentation.slot import Slot
from cardwork.states.award import Award
from cardwork.zones.zone import ZoneId


class Layout(BaseFrozen):
    """Everything an interface needs to lay a game out for one seat, and nothing about how it looks.

    A game states one of these per observer, so every zone id, seat and gesture in it is concrete and the
    interface resolves nothing: it draws the slots where they belong, matches the moves it is served to the
    gestures, reads the cursor through the readouts and captions the phase from `phases`. What is left over —
    the size of a card, the colour of a highlight, the moment a heap collapses — is the interface's own.

    The line runs between which thing is meant and what it looks like: a plaque states which of eight tints a
    player is told apart by, and what that tint draws as belongs to the interface, exactly as a spread states
    how cards lie against each other and where they lie belongs to the page.

    Every claim a layout makes about itself is checked as it is built, which leaves an interface free to trust
    it: one slot per zone, a slot belonging to a seat of the table or to the table itself, one slot per place
    among the slots of one owner, one plaque per seat, one gesture per move, every zone a gesture names laid
    out as a slot the player can reach, and a phase play pauses at captioned like any other.
    """

    title: str
    observer: int | None
    players: int = Field(ge=1)
    slots: tuple[Slot, ...]
    gestures: tuple[Gesture, ...]
    plaques: tuple[Plaque, ...]
    readouts: tuple[Readout, ...]
    phases: Mapping[str, str]
    interludes: Mapping[str, Interlude]
    award: Award
    cues: bool = True

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
    def _every_slot_belongs_to_the_table(self) -> Self:
        """Confirm each slot belongs to a seat of the table, or to the table itself.

        Raises:
            ValueError: when a slot names an owner the table holds no seat for.
        """
        unseated = distinct(
            tuple(slot.seat for slot in self.slots if slot.seat is not None and not 0 <= slot.seat < self.players)
        )
        if unseated:
            raise ValueError(
                f"A slot belongs to one of the {self.players} seats or to the table, and these name: {unseated}"
            )

        return self

    @model_validator(mode="after")
    def _every_place_holds_one_slot(self) -> Self:
        """Confirm the slots of one owner fall in a settled order.

        Raises:
            ValueError: when two slots of one owner take the same place.
        """
        twice = repeated(tuple((slot.seat, slot.place) for slot in self.slots))
        if twice:
            raise ValueError(f"A place among one owner's slots holds one slot, and these hold two apiece: {twice}")

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
        refusal = mismatched(tuple((gesture.kind, gesture.group) for gesture in self.gestures))
        if refusal is not None:
            raise ValueError(refusal)

        return self

    @model_validator(mode="after")
    def _every_gesture_reaches_its_zones(self) -> Self:
        """Confirm a player can point at the cards a gesture picks and the zone it commits onto.

        A gesture answers for the zones it names, so one made in no zone and one landing on none are held to
        nothing here: a pass reaches a player by its own caption rather than by a zone drawn for it.

        Raises:
            ValueError: when a gesture picks from or commits onto a zone no slot lays out.
        """
        laid = {slot.zone for slot in self.slots}
        self._laid_out(
            tuple(gesture.picked for gesture in self.gestures if gesture.picked is not None),
            laid,
            "picked from",
        )
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
        refusal = misread(self.readouts)
        if refusal is not None:
            raise ValueError(refusal)

        return self

    @model_validator(mode="after")
    def _every_interlude_names_a_captioned_phase(self) -> Self:
        """Confirm a phase play pauses at is one the layout states words for.

        Raises:
            ValueError: when an interlude names a phase the captions leave out.
        """
        refusal = uncaptioned(self.interludes, self.phases)
        if refusal is not None:
            raise ValueError(refusal)

        return self

    @staticmethod
    def _laid_out(named: tuple[ZoneId, ...], laid: set[ZoneId], reached: str) -> None:
        """Confirm every zone a gesture names is one the slots lay out.

        Raises:
            ValueError: when a named zone takes no slot.
        """
        missing = distinct(tuple(zone for zone in named if zone not in laid))
        if missing:
            raise ValueError(f"A zone {reached} takes a slot of its own, and these take none: {missing}")
