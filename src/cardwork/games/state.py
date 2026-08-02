from pydantic import Field

from cardwork.models.base import BaseFrozen


class GameState(BaseFrozen):
    phase: str
    to_act: frozenset[int] = Field(default_factory=frozenset)
    points: list[int] | None = Field(default=None)

    @property
    def current(self) -> int | None:
        """The single player to act, or None if this is not a sequential phase."""
        return next(iter(self.to_act)) if len(self.to_act) == 1 else None
