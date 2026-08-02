from cardwork.zones.audience import Audience
from cardwork.zones.visibility import Visibility

HAND = Visibility(face_up=Audience.ALL, face_down=Audience.OWNER)
PILE = Visibility(face_up=Audience.ALL, face_down=Audience.NONE)
HIDDEN = Visibility(face_up=Audience.NONE, face_down=Audience.NONE)
