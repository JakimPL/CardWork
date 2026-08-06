from enum import StrEnum


class Commit(StrEnum):
    """How a player sends the move a selection has armed.

    `ZONE` sends it onto a zone of the table — the pile a card is exchanged with, the tray it is sealed in —
    which the gesture names. `SEAT` sends it onto another player, whom the move itself names. Both are places
    on the table, so a move naming cards is committed by pointing at where those cards go, and a selection
    alone commits nothing.

    `WORD` is the third answer, for a move a place on the table stands for none of: a turn given up names no
    card and no destination, so a seat says it rather than points at it. A gesture committing this way names
    no target, and an interface draws it as somewhere to press rather than as a place cards travel to.

    A game whose move carries a decision of its own — a bid, a trump chosen, a contract announced — is said
    the same way, which is what `Declare` is waiting on (`architecture.md` §5.3).
    """

    ZONE = "zone"
    SEAT = "seat"
    WORD = "word"
