from cardserver.errors import NoSay
from cardserver.gathering.gathering import Gathering


class GovernedSay:
    """A say read through how each table is governed, which the company settles for itself.

    A table governed democratically gives its say to every guest holding a seat: standing is watching and
    taking a seat is joining the game, so the players settle what is played and a standing guest is told rather
    than obeyed. A table governed by its host gives the say to the host alone, and a seated guest who is not the
    host is told the same as one standing. Which of the two a table is stands on the table, not on the policy,
    so one policy answers for every table this host holds however each of them is run.
    """

    def confirm(self, gathering: Gathering, guest: str) -> None:
        """Confirm the guest holds a say at this gathering, as the way it is governed reads it.

        Raises:
            NoSay: when the table is democratic and the guest holds no seat, or is governed by its host and the
                guest is a seated player who is not that host.
        """
        if gathering.democratic:
            if gathering.seat_of(guest) is None:
                raise NoSay(guest)

            return

        if guest != gathering.host:
            raise NoSay(guest)
