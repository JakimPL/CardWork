from cardserver.errors import WrongSeat


def seated(observer: int | None) -> int:
    """The seat behind a command that a seat of the table alone may send.

    A command naming no seat of its own is one the credential answers for entirely, so the seat it lands for
    is read here rather than confirmed. Both commands pass through this, which is what leaves one answer for
    the client holding no seat at all.

    Raises:
        WrongSeat: when a spectator sends a command, since watching a table is done at no seat of it.
    """
    if observer is None:
        raise WrongSeat("A spectator watches the table and acts at no seat of it")

    return observer


def confirm_actor(observer: int | None, player: int) -> None:
    """Confirm the client behind a command holds the seat the move was made for.

    The engine trusts `move.player`, so the seat it names is settled here, where a credential is all
    the server knows of who is asking.

    Raises:
        WrongSeat: when a spectator submits a command, or when a seat submits one made for another.
    """
    held = seated(observer)
    if held != player:
        raise WrongSeat(f"The credential holds seat {held}, and the move was made for seat {player}")
