from pathlib import Path
from typing import Final

REPOSITORY: Final[Path] = Path(__file__).resolve().parents[2]
ASSETS: Final[Path] = REPOSITORY / "assets"
FRONTEND: Final[Path] = REPOSITORY / "frontend"
INTERFACE: Final[Path] = FRONTEND / "dist"
