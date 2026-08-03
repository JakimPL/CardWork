from enum import StrEnum


class Commit(StrEnum):
    """The place a player points at to send the move a selection has armed.

    `ZONE` sends it onto a zone of the table — the pile a card is exchanged with, the tray it is sealed in —
    which the gesture names. `SEAT` sends it onto another player, whom the move itself names.

    Both are places on the table, so a move is committed by pointing at where it goes and a selection alone
    commits nothing. A game whose move carries a decision that no place on the table stands for — a bid, a
    trump chosen, a contract announced — gains a member here the day it is written.
    """

    ZONE = "zone"
    SEAT = "seat"
