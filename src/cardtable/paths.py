from pathlib import Path
from typing import Final

REPOSITORY: Final[Path] = Path(__file__).resolve().parents[2]
CONFIGURATION: Final[Path] = REPOSITORY / "config.yaml"
ASSETS: Final[Path] = REPOSITORY / "assets"
RECORDS: Final[Path] = REPOSITORY / "records"
FRONTEND: Final[Path] = REPOSITORY / "frontend"
INTERFACE: Final[Path] = FRONTEND / "dist"
SPECIFICATION: Final[Path] = FRONTEND / "openapi.json"
