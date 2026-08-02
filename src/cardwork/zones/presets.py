from typing import Final

from cardwork.zones.audience import Audience
from cardwork.zones.visibility import Visibility

HAND: Final[Visibility] = Visibility(face_up=Audience.ALL, face_down=Audience.OWNER)
PILE: Final[Visibility] = Visibility(face_up=Audience.ALL, face_down=Audience.NONE)
HIDDEN: Final[Visibility] = Visibility(face_up=Audience.NONE, face_down=Audience.NONE)
