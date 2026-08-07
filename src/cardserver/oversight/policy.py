from typing import Protocol


class AdminPolicy(Protocol):
    """How this deployment tells its overseer apart from everyone else, which is the one privilege above a seat.

    Overseeing is the only thing here no code and no seat admits anyone to, so the whole of it sits behind this
    call: a credential is confirmed to be the overseer's or the request is turned away before it is read.
    """

    def confirm(self, credential: str | None) -> None:
        """Confirm this credential is the one this host oversees under.

        Raises:
            Unauthorized: when no credential was offered, or one that is not this host's.
        """
