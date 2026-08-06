from collections.abc import Callable

from cardwork.models.held import held


def next_seat(seat: int, players: int) -> int:
    """The seat next round the table, counting on from this one and wrapping at the last."""
    return (seat + 1) % players


def rotation(leader: int, players: int) -> tuple[int, ...]:
    """Every seat from the leader round the table, which is the order a round deals, plays and reveals in."""
    return tuple((leader + step) % players for step in range(players))


def following(
    seat: int,
    players: int,
    admits: Callable[[int], bool],
    *,
    including: bool,
) -> int | None:
    """The first seat round the table the question admits, or None where no seat at the table does.

    A rule that hands the turn to the seat able to take it states the condition and reads the seat back from
    here, which leaves the walk round the table in one place and the rule about the seats it is looking for.

    Args:
        seat: the seat the search sets out from.
        players: how many seats the table holds.
        admits: whether one seat is a seat the search is looking for.
        including: whether the seat set out from answers for itself, which tells a turn that may stay where
            it stands apart from one that travels on.
    """
    start = seat if including else next_seat(seat, players)
    return next((other for other in rotation(start, players) if admits(other)), None)


def followed(
    seat: int,
    players: int,
    admits: Callable[[int], bool],
    *,
    including: bool,
) -> int:
    """The first seat round the table the question admits, where the rules hold that one of them does.

    `following` answers with None for a table no seat of which is admitted, which a rule carrying the turn on
    reads as the round it closes. This is for the rule that has already settled a seat stands there.

    Args:
        seat: the seat the search sets out from.
        players: how many seats the table holds.
        admits: whether one seat is a seat the search is looking for.
        including: whether the seat set out from answers for itself.

    Raises:
        LogicError: when no seat at the table is admitted.
    """
    return held(
        following(seat, players, admits, including=including),
        f"seat of the {players} at this table follows seat {seat}",
    )
