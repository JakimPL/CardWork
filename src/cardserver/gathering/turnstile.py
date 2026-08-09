from __future__ import annotations

from collections.abc import Callable

from cardserver.errors import Unadmitted


class Turnstile:
    """How many wrong codes one caller may offer before a gathering stops listening to it.

    Six ranks name some millions of hands, which is a number a program reaches and a person does not, so what
    guards a code is the rate rather than the length. Every refusal is remembered against the address it came
    from for as long as the window runs, and an address past its allowance is turned away before the code it
    offers is read at all.

    The address is the one the connection carries, so callers reaching the server through one proxy are counted
    as one caller. That is the honest reading of what a server knows of where a request came from.
    """

    def __init__(
        self,
        allowed: int,
        window: float,
        clock: Callable[[], float],
    ) -> None:
        self._allowed = allowed
        self._window = window
        self._clock = clock
        self._refusals: dict[str, tuple[float, ...]] = {}

    @classmethod
    def watching(
        cls,
        clock: Callable[[], float],
        *,
        window: float,
        wrong_codes_allowed: int,
    ) -> Turnstile:
        """A turnstile at the allowance a run keeps, reading the time off one clock.

        Args:
            clock: where the current time is read from, which a window is measured against.
            window: how long a wrong code is counted against the address that offered it.
            wrong_codes_allowed: how many wrong codes an address may offer inside the window before it waits.
        """
        return cls(wrong_codes_allowed, window, clock)

    def confirm(self, caller: str) -> None:
        """Confirm this caller may offer a code.

        Raises:
            Unadmitted: when the caller has offered more wrong codes than the window allows.
        """
        if len(self._recent(caller)) >= self._allowed:
            raise Unadmitted("Too many wrong codes came from this address, so wait a moment and offer it again")

    def refused(self, caller: str) -> None:
        """Remember one wrong code against the caller that offered it."""
        self._refusals[caller] = (*self._recent(caller), self._clock())

    def _recent(self, caller: str) -> tuple[float, ...]:
        """The refusals of one caller still inside the window, which is what an allowance counts."""
        since = self._clock() - self._window
        return tuple(at for at in self._refusals.get(caller, ()) if at > since)
