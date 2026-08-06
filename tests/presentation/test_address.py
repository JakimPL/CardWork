from typing import Final

from cardwork.presentation.address import at, word_of
from cardwork.zones.family import Family
from cardwork.zones.presets import HAND
from cardwork.zones.zone import Zone, ZoneId

SEAT: Final[int] = 2
SEATS: Final[int] = 3
STOCK: Final[ZoneId] = "stock"
TRAYS: Final[Family] = Family(name="tray", ordered=True, visibility=HAND)


def test_a_family_names_the_zone_it_stands_at_the_seat_asked_for() -> None:
    assert at(TRAYS, SEAT) == TRAYS.of(SEAT)


def test_a_zone_of_the_table_names_itself_at_every_seat() -> None:
    assert at(STOCK, SEAT) == STOCK


def test_the_zone_a_family_names_is_the_one_it_stands_on_the_table() -> None:
    laid = TRAYS.zones(SEATS)

    assert laid[at(TRAYS, SEAT)] == Zone(id=TRAYS.of(SEAT), owner=SEAT, visibility=HAND, ordered=True)


def test_a_family_travels_under_its_own_name() -> None:
    assert word_of(TRAYS) == TRAYS.name


def test_a_zone_of_the_table_travels_under_its_id() -> None:
    assert word_of(STOCK) == STOCK
