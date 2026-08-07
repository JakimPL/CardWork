from typing import Final

from cardwork.presentation.tint import Tint

# TODO: move variables to advanced server configuration; define constants in appropriate modules
TOKEN_BYTES: Final[int] = 32
TINTS: Final[tuple[Tint, ...]] = tuple(Tint)
COMPANY_MOST: Final[int] = len(TINTS)
WRONG_CODES_ALLOWED: Final[int] = 10
TURNSTILE_WINDOW: Final[float] = 60.0
FIRST_REVISION: Final[int] = 0
STANDING: Final[None] = None
DEMOCRATIC: Final[bool] = True
NO_LIMIT: Final[int] = 0
