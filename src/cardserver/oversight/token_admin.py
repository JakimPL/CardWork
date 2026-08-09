from secrets import compare_digest

from cardserver.errors import Unauthorized


class TokenAdmin:
    """An overseer known by one opaque token, which this host is handed as it starts and hands to nobody else.

    The token is a hand of random bytes rather than a word anyone chooses, so there is nothing to guess and no
    door to knock on: a request either carries the token the host was started under or it is turned away. The
    two are compared under `compare_digest`, which takes the same time whatever they hold, so a wrong token
    learns nothing of how much of it was right.
    """

    def __init__(self, token: str) -> None:
        self._token = token

    def confirm(self, credential: str | None) -> None:
        """Confirm the credential is the token this host was started under.

        Raises:
            Unauthorized: when none was offered, or one that is not the host's.
        """
        if credential is None or not compare_digest(credential, self._token):
            raise Unauthorized()
