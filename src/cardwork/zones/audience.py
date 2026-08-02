from enum import StrEnum


class Audience(StrEnum):
    ALL = "all"
    OWNER = "owner"
    NONE = "none"
