from collections.abc import Mapping
from typing import Final

from cardserver.naming import Named
from cardwork.presentation.scene import SEAT_NAME

from ..games.demo import SEATS
from .layout import SEALED_SCENE

NAMES: Final[Mapping[int, str]] = {0: "Ada", 2: "Grace"}
WATCHING: Final[None] = None


def named_at(seat: int, observer: int | None) -> str:
    """The name one seat is read by on the plaques of a layout drawn for that observer."""
    layout = Named(SEALED_SCENE, NAMES).layout(SEATS, observer)
    return next(plaque.name for plaque in layout.plaques if plaque.seat == seat)


def test_a_seat_is_read_by_the_name_its_guest_arrived_under() -> None:
    assert named_at(0, 0) == "Ada"
    assert named_at(2, 0) == "Grace"


def test_a_seat_the_gathering_named_nobody_at_is_read_by_where_it_sits() -> None:
    assert named_at(1, 0) == SEAT_NAME.format(seat=1)


def test_every_observer_reads_the_same_names_across_the_table() -> None:
    assert named_at(0, 2) == "Ada"
    assert named_at(0, WATCHING) == "Ada"


def test_naming_the_seats_leaves_the_rest_of_a_layout_as_the_scene_laid_it_out() -> None:
    drawn = SEALED_SCENE.layout(SEATS, 0)
    named = Named(SEALED_SCENE, NAMES).layout(SEATS, 0)

    assert named.model_copy(update={"plaques": drawn.plaques}) == drawn


def test_a_plaque_goes_on_counting_what_it_counted_before_it_was_named() -> None:
    drawn = SEALED_SCENE.layout(SEATS, 0)
    named = Named(SEALED_SCENE, NAMES).layout(SEATS, 0)

    assert tuple(plaque.counts for plaque in named.plaques) == tuple(plaque.counts for plaque in drawn.plaques)
