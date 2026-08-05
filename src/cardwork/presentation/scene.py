from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final

from cardwork.presentation.fixture import Fixture
from cardwork.presentation.gesture import Gesture
from cardwork.presentation.interlude import Interlude
from cardwork.presentation.layout import Layout
from cardwork.presentation.plaque import Plaque
from cardwork.presentation.readout import Readout
from cardwork.presentation.setting import Setting
from cardwork.presentation.slot import Slot
from cardwork.presentation.tally import Tally
from cardwork.states.award import Award

SEAT_NAME: Final[str] = "Seat {seat}"


@dataclass(frozen=True)
class Scene:
    """How a game is laid out, stated once for a table rather than once for every observer of it.

    A game states one of these and each observer's `Layout` follows from it. `table` holds the zones of the
    table, which every observer reads the same way, and `seated` the zone families its seats hold, each stated
    once for every seat at once. So the layout of an observer is its own zones, the rest of the table read at
    every seat beside it, and the zones of the table besides. `title`, `readouts`, `phases`, `interludes` and
    `award` stand the same for everybody: what a match comes to is one thing every seat reads alike.

    A `Setting` states its family under as many lays as the family has readers — the cards a hand shows itself
    are backs to the table, and a holding it counts by looking carries its size across the table instead — and
    a seat's zones stand in the run the scene names them in.

    What a layout owes its observer is stated here once instead of in every game: a seat reads the zones it
    holds beside the zones of the table and is offered the gestures of its own turn, a spectator reads every
    seat as the table reads it and makes no move, and every seat of the table takes a plaque whether anybody is
    sitting at it.
    """

    title: str
    table: tuple[Fixture, ...]
    seated: tuple[Setting, ...]
    gestures: Callable[[int], tuple[Gesture, ...]]
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
        """The gestures an observer makes its moves with.

        Returns:
            The seat's own gestures, and nothing for a spectator, who makes no move.
        """
        return self.gestures(observer) if observer is not None else ()

    def _plaques(self, players: int) -> tuple[Plaque, ...]:
        """A plaque for every seat of the table, counting the zones that seat holds.

        A seat is named by where it sits, which is the whole of what a table knows of a player until a host
        holds a name for one.
        """
        return tuple(
            Plaque(
                seat=seat,
                name=SEAT_NAME.format(seat=seat),
                counts=self._counted_at(seat),
            )
            for seat in range(players)
        )

    def _counted_at(self, seat: int) -> tuple[Tally, ...]:
        """What the plaque of one seat counts, which is every family of its own that carries a word for its size."""
        counted = (setting.counted_at(seat) for setting in self.seated)
        return tuple(tally for tally in counted if tally is not None)
