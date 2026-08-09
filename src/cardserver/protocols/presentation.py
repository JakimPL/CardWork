from typing import Protocol

from cardwork.presentation.layout import Layout


class Presentation(Protocol):
    """Everything the adapter asks of a game's arrangement in order to serve it.

    A table reaches a screen as two answers: the projection of its cards, which the rules produce, and the
    layout an interface draws them into, which is stated apart from them. This is the whole of what a
    transport touches of the second, and it stands beside `Table` for the same reason — the port belongs to
    the consumer, which leaves the presentation layer free of any mention that a transport exists.

    `cardwork.presentation.Scene` satisfies it, and so does anything else a host holds a table's arrangement
    in: the layout of one observer is all that is asked for.
    """

    def layout(self, players: int, observer: int | None) -> Layout:
        """How a table of that many seats is laid out for one observer, or for a spectator holding none."""
