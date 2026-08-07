from typing import Protocol

from cardserver.gathering.gathering import Gathering


class SayPolicy(Protocol):
    """Which guests hold a say over what a table plays and when it is dealt.

    Who settles a game is a question about the company rather than about the rules, so it stands behind a call
    of its own: a table among friends asks only that a guest is sitting at it, and a deployment holding accounts
    or groups answers the same call out of what it knows of them.
    """

    def confirm(self, gathering: Gathering, guest: str) -> None:
        """Confirm this guest holds a say at this gathering.

        Raises:
            NoSay: when the guest holds none.
        """
