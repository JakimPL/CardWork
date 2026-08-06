from collections.abc import Mapping
from typing import Final, Self

from pydantic import model_validator

from cardwork.models.base import BaseFrozen
from cardwork.presentation.address import Address, word_of
from cardwork.presentation.fixture import Fixture
from cardwork.presentation.gesture import Gesture, mismatched
from cardwork.presentation.interlude import Interlude, uncaptioned
from cardwork.presentation.layout import Layout
from cardwork.presentation.making import Making
from cardwork.presentation.plaque import Plaque
from cardwork.presentation.readout import Readout, misread
from cardwork.presentation.repeats import distinct
from cardwork.presentation.setting import Setting
from cardwork.presentation.slot import Slot
from cardwork.presentation.tally import Tally
from cardwork.states.award import Award

SEAT_NAME: Final[str] = "Seat {seat}"
UNTINTED: Final[None] = None


class Scene(BaseFrozen):
    """How a game is laid out, stated once for a table rather than once for every observer of it.

    A game states one of these and each observer's `Layout` follows from it. `table` holds the zones of the
    table, which every observer reads the same way, `seated` the zone families its seats hold, and `gestures`
    the moves a seat makes, each of the three stated once for every seat at once. So the layout of an observer
    is its own zones, the rest of the table read at every seat beside it, the zones of the table besides, and
    the moves of its own turn. `title`, `readouts`, `phases`, `interludes` and `award` stand the same for
    everybody: what a match comes to is one thing every seat reads alike.

    A `Setting` states its family under as many lays as the family has readers — the cards a hand shows itself
    are backs to the table, and a holding it counts by looking carries its size across the table instead — and
    a seat's zones stand in the run the scene names them in.

    What a layout owes its observer is stated here once instead of in every game: a seat reads the zones it
    holds beside the zones of the table and is offered the gestures of its own turn, a spectator reads every
    seat as the table reads it and makes no move, and every seat of the table takes a plaque whether anybody is
    sitting at it. A scene answers for the whole of that as it is stated, so a game hears about a mistake where
    it wrote one.
    """

    title: str
    table: tuple[Fixture, ...]
    seated: tuple[Setting, ...]
    gestures: tuple[Making, ...]
    readouts: tuple[Readout, ...]
    phases: Mapping[str, str]
    interludes: Mapping[str, Interlude]
    award: Award

    def layout(self, players: int, observer: int | None) -> Layout:
        """The layout one observer of a table that size reads the game through.

        This is what an interface is served, and what the adapter answers a request for a layout with. The
        entitlement it carries is the one the projection gives the same observer over the cards
        (`architecture.md` §7): its own zones and its own moves, the other seats as the table reads them, and
        the shared table besides.

        Args:
            players: how many seats the table holds.
            observer: the seat the layout is built for, or None for a spectator.
        """
        return Layout(
            title=self.title,
            observer=observer,
            players=players,
            slots=self._held_by(observer) + self._seen_around(players, observer) + self._shared(),
            gestures=self._offered_to(observer),
            plaques=self._plaques(players),
            readouts=self.readouts,
            phases=self.phases,
            interludes=self.interludes,
            award=self.award,
        )

    def _held_by(self, observer: int | None) -> tuple[Slot, ...]:
        """The zones an observer holds of its own, as that observer reads them.

        Returns:
            The seat's own zones, and nothing for a spectator, who holds none.
        """
        if observer is None:
            return ()

        drawn = (setting.held_at(observer, place) for place, setting in enumerate(self.seated))
        return tuple(slot for slot in drawn if slot is not None)

    def _seen_around(self, players: int, observer: int | None) -> tuple[Slot, ...]:
        """The zones of every seat beside the observer, as the rest of the table reads them.

        Args:
            players: how many seats the table holds.
            observer: the seat reading the layout, whose own zones `_held_by` answers for instead.
        """
        return tuple(slot for seat in range(players) if seat != observer for slot in self._seen_at(seat))

    def _seen_at(self, seat: int) -> tuple[Slot, ...]:
        """The zones of one seat as the rest of the table reads them."""
        drawn = (setting.seen_at(seat, place) for place, setting in enumerate(self.seated))
        return tuple(slot for slot in drawn if slot is not None)

    def _shared(self) -> tuple[Slot, ...]:
        """The zones of the table, standing in the run the scene names them in."""
        return tuple(fixture.slot(place) for place, fixture in enumerate(self.table))

    def _offered_to(self, observer: int | None) -> tuple[Gesture, ...]:
        """The gestures an observer makes its moves with, which are the moves of the scene bound to that seat.

        Returns:
            The seat's own gestures, and nothing for a spectator, who makes no move.
        """
        if observer is None:
            return ()

        return tuple(making.gesture(observer) for making in self.gestures)

    def _plaques(self, players: int) -> tuple[Plaque, ...]:
        """A plaque for every seat of the table, counting the zones that seat holds.

        A seat is named by where it sits and plays under no tint, which is the whole of what a table knows of a
        player until a host holds a name and a tint for one.
        """
        return tuple(
            Plaque(
                seat=seat,
                name=SEAT_NAME.format(seat=seat),
                tint=UNTINTED,
                counts=self._counted_at(seat),
            )
            for seat in range(players)
        )

    def _counted_at(self, seat: int) -> tuple[Tally, ...]:
        """What the plaque of one seat counts, which is every family of its own that carries a word for its size."""
        counted = (setting.counted_at(seat) for setting in self.seated)
        return tuple(tally for tally in counted if tally is not None)

    @model_validator(mode="after")
    def _the_scene_answers_for_the_layouts_drawn_from_it(self) -> Self:
        """Confirm what every observer's layout is held to, which a scene states once for all of them.

        A `Layout` holds each of these claims of its own, since it stands alone whoever built it. Stating them
        here as well is what lets a game read a refusal as its module loads rather than once a table is served,
        and the words are the same either way.

        Raises:
            ValueError: when two gestures answer one move, when a gesture names a zone the scene lays out
                nowhere, when a field of the cursor reads twice, or when a phase play pauses at is uncaptioned.
        """
        refusals = (
            mismatched(tuple(making.matching for making in self.gestures)),
            self._unreachable(),
            misread(self.readouts),
            uncaptioned(self.interludes, self.phases),
        )
        for refusal in refusals:
            if refusal is not None:
                raise ValueError(refusal)

        return self

    def _unreachable(self) -> str | None:
        """Which zone a gesture names that the scene lays out nowhere, and None where each of them takes a slot.

        A move picks its cards up in one zone and puts them down in another, and a player points at both, so
        each is a family the seat making the move holds or a zone of the table.
        """
        reached = self._reachable()
        named = tuple(
            address for making in self.gestures for address in (making.picked, making.target) if address is not None
        )
        missing = distinct(tuple(word_of(address) for address in named if address not in reached))
        if missing:
            return f"A zone a gesture names is one the scene lays out, and these take no slot: {missing}"

        return None

    def _reachable(self) -> tuple[Address, ...]:
        """What a seat reaches: the families it reads a zone of its own by, and the zones of the table."""
        held = tuple(setting.family for setting in self.seated if setting.held is not None)
        return held + tuple(fixture.zone for fixture in self.table)
