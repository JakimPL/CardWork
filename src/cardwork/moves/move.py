from pydantic import Field

from cardwork.models.base import BaseFrozen
from cardwork.moves.actions import Action


class Move(BaseFrozen):
    player: int = Field(ge=-1)
    action: Action


Moves = tuple[Move, ...]
