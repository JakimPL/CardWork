from collections.abc import Mapping
from secrets import token_urlsafe
from typing import Final

TOKEN_BYTES: Final[int] = 8


def tokens_for(players: int) -> Mapping[int, str]:
    """One token per seat of a table, each standing for whoever opens the interface holding it.

    A token is the whole of what this host knows of a player: it is handed out once as the table opens, and
    a client offering it is served that seat's own cards and that seat's own moves. A client offering none
    watches the table as a spectator, which is what leaves a game open to look at.
    """
    return {seat: token_urlsafe(TOKEN_BYTES) for seat in range(players)}
