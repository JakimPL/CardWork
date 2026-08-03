from enum import StrEnum


class Region(StrEnum):
    """Where on the screen a zone is laid out, which is the whole of the geography a game states.

    A `TABLE` zone is one the seats share and every one of them reads the same way: the pile dealt from, the
    stack laid on. A `SEAT` zone belongs to the observer the layout was built for, and holds the cards that
    observer acts with. Where each region sits on the page and how much of it a card takes belongs to the
    interface, which is why two names carry the whole of it.
    """

    TABLE = "table"
    SEAT = "seat"
