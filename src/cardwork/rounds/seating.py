def next_seat(seat: int, players: int) -> int:
    """The seat next round the table, counting on from this one and wrapping at the last."""
    return (seat + 1) % players


def rotation(leader: int, players: int) -> tuple[int, ...]:
    """Every seat from the leader round the table, which is the order a round deals, plays and reveals in."""
    return tuple((leader + step) % players for step in range(players))
