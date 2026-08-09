from cardserver.schemas.gathering import GatheringView
from cardwork.models.base import BaseFrozen


class Admitted(BaseFrozen):
    """What a guest is answered on arrival: the token they speak through, and the gathering they have joined.

    The token is the whole of what this server knows of them. It rides the fragment of an address, which a
    browser sends to nobody, and reaches every endpoint in a header of its own.
    """

    token: str
    gathering: GatheringView
