from pydantic import Field

from cardwork.models.base import BaseFrozen


class GameState(BaseFrozen):
    player: int = Field(ge=0)
    points: list[int] | None = Field(default=None)
