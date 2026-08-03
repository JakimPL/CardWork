from typing import Final

from cardtable.paths import ASSETS, FRONTEND, INTERFACE, REPOSITORY

MANIFEST: Final[str] = "pyproject.toml"
PACKAGES: Final[str] = "src"
BUILD: Final[str] = "dist"


def test_the_repository_is_the_checkout_the_host_is_read_from() -> None:
    assert (REPOSITORY / MANIFEST).is_file()
    assert (REPOSITORY / PACKAGES).is_dir()


def test_the_assets_stand_in_the_repository() -> None:
    assert ASSETS.parent == REPOSITORY


def test_the_frontend_stands_in_the_repository() -> None:
    assert FRONTEND.parent == REPOSITORY


def test_the_interface_is_a_build_of_the_frontend() -> None:
    assert INTERFACE.parent == FRONTEND
    assert INTERFACE.name == BUILD
