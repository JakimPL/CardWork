from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final

from cardwork.presentation.gesture import Gesture
from cardwork.presentation.layout import Layout
from cardwork.presentation.plaque import Plaque
from cardwork.presentation.readout import Readout
from cardwork.presentation.slot import Slot
from cardwork.presentation.tally import Tally

SEAT_NAME: Final[str] = "Seat {seat}"


@dataclass(frozen=True)
class Scene:
    """How a game is laid out, stated once for a table rather than once for every observer of it.

    A game states one of these and each observer's `Layout` follows from it. `shared` holds the zones every
    observer reads the same way, and `held`, `seen`, `gestures` and `counts` each answer for one seat, so the
    layout of an observer is its own zones, the rest of the table read at every seat beside it, and the shared
    zones besides. `title`, `readouts` and `phases` stand the same for everybody.

    `held` states a seat's zones as that seat reads them, and `seen` the same zones as everybody else does: the
    cards a hand shows itself are backs to the table, and a holding it counts by looking carries its size across
    the table instead. A game leaves a zone off the table by omitting it from `seen`, where a `Tally` on the
    plaque still carries how much of it there is.

    What a layout owes its observer is stated here once instead of in every game: a seat reads the zones it
    holds beside the shared ones and is offered the gestures of its own turn, a spectator reads every seat as
    the table reads it and makes no move, and every seat of the table takes a plaque whether anybody is sitting
    at it.
    """

    title: str
    shared: tuple[Slot, ...]
    held: Callable[[int], tuple[Slot, ...]]
    seen: Callable[[int], tuple[Slot, ...]]
    gestures: Callable[[int], tuple[Gesture, ...]]
    counts: Callable[[int], tuple[Tally, ...]]
    readouts: tuple[Readout, ...]
    phases: Mapping[str, str]

    def __post_init__(self) -> None:
        """Confirm the zones the table shares belong to no seat, since every observer reads them alike.

        Raises:
            ValueError: when a shared slot names a seat as its owner.
        """
        owned = tuple(slot.zone for slot in self.shared if slot.seat is not None)
        if owned:
            raise ValueError(f"A zone the table shares belongs to no seat, and these name one: {owned}")

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
            slots=self._held_by(observer) + self._seen_around(players, observer) + self.shared,
            gestures=self._offered_to(observer),
            plaques=self._plaques(players),
            readouts=self.readouts,
            phases=self.phases,
        )

    def _held_by(self, observer: int | None) -> tuple[Slot, ...]:
        """The zones an observer holds of its own, as that observer reads them.

        Returns:
            The seat's own zones, and nothing for a spectator, who holds none.
        """
        return self._owned(self.held, observer) if observer is not None else ()

    def _seen_around(self, players: int, observer: int | None) -> tuple[Slot, ...]:
        """The zones of every seat beside the observer, as the rest of the table reads them.

        Args:
            players: how many seats the table holds.
            observer: the seat reading the layout, whose own zones `held` answers for instead.
        """
        return tuple(slot for seat in range(players) if seat != observer for slot in self._owned(self.seen, seat))

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
                counts=self.counts(seat),
            )
            for seat in range(players)
        )

    @staticmethod
    def _owned(drawn: Callable[[int], tuple[Slot, ...]], seat: int) -> tuple[Slot, ...]:
        """The slots one of the scene's functions lays out for a seat, each of them naming that seat.

        Args:
            drawn: the zones of one seat, read either as that seat reads them or as the table does.
            seat: the seat they were asked for, which is the owner every slot of them belongs to.

        Raises:
            ValueError: when a slot names an owner other than the seat it was laid out for.
        """
        slots = drawn(seat)
        astray = tuple(slot.zone for slot in slots if slot.seat != seat)
        if astray:
            raise ValueError(f"A zone laid out for seat {seat} belongs to it, and these name another: {astray}")

        return slots
