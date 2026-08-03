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
    observer reads the same way, and `held`, `gestures` and `counts` each answer for one seat, so the layout
    of an observer is those three read at its own seat. `title`, `readouts` and `phases` stand the same for
    everybody.

    What a layout owes its observer is stated here once instead of in every game: a seat reads the zones it
    holds beside the shared ones and is offered the gestures of its own turn, a spectator reads the shared
    zones and makes no move, and every seat of the table takes a plaque whether anybody is sitting at it.
    """

    title: str
    shared: tuple[Slot, ...]
    held: Callable[[int], tuple[Slot, ...]]
    gestures: Callable[[int], tuple[Gesture, ...]]
    counts: Callable[[int], tuple[Tally, ...]]
    readouts: tuple[Readout, ...]
    phases: Mapping[str, str]

    def layout(self, players: int, observer: int | None) -> Layout:
        """The layout one observer of a table that size reads the game through.

        This is what an interface is served, and what the adapter answers a request for a layout with. The
        entitlement it carries is the one the projection gives the same observer over the cards
        (`architecture.md` §7): its own zones and its own moves, and the shared table besides.

        Args:
            players: how many seats the table holds.
            observer: the seat the layout is built for, or None for a spectator.
        """
        return Layout(
            title=self.title,
            observer=observer,
            players=players,
            slots=self._held_by(observer) + self.shared,
            gestures=self._offered_to(observer),
            plaques=self._plaques(players),
            readouts=self.readouts,
            phases=self.phases,
        )

    def _held_by(self, observer: int | None) -> tuple[Slot, ...]:
        """The zones an observer holds of its own.

        Returns:
            The seat's own zones, and nothing for a spectator, whose seat region stands empty.
        """
        return self.held(observer) if observer is not None else ()

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
