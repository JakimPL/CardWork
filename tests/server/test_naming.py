from collections.abc import Mapping
from typing import Final

from cardserver.naming import Named, Seated
from cardwork.presentation.plaque import Plaque
from cardwork.presentation.scene import SEAT_NAME
from cardwork.presentation.tint import Tint

from ..games.demo import SEATS
from .layout import SEALED_SCENE

SEATED: Final[Mapping[int, Seated]] = {
    0: Seated(name="Ada", tint=Tint.ROSE),
    2: Seated(name="Grace", tint=Tint.TEAL),
}
WATCHING: Final[None] = None
UNTINTED: Final[None] = None


def named_at(seat: int, observer: int | None) -> str:
    """The name one seat is read by on the plaques of a layout drawn for that observer."""
    return _plaque_at(seat, observer).name


def tinted_at(seat: int, observer: int | None) -> Tint | None:
    """The tint one seat plays under on the plaques of a layout drawn for that observer."""
    return _plaque_at(seat, observer).tint


def test_a_seat_is_read_by_the_name_its_guest_arrived_under() -> None:
    assert named_at(0, 0) == "Ada"
    assert named_at(2, 0) == "Grace"


def test_a_seat_plays_under_the_tint_the_company_tells_its_guest_apart_by() -> None:
    assert tinted_at(0, 0) == Tint.ROSE
    assert tinted_at(2, 0) == Tint.TEAL


def test_a_seat_the_gathering_named_nobody_at_is_read_by_where_it_sits() -> None:
    assert named_at(1, 0) == SEAT_NAME.format(seat=1)
    assert tinted_at(1, 0) is UNTINTED


def test_every_observer_reads_the_same_names_across_the_table() -> None:
    assert named_at(0, 2) == "Ada"
    assert named_at(0, WATCHING) == "Ada"


def test_every_observer_reads_the_same_tints_across_the_table() -> None:
    assert tinted_at(0, 2) == Tint.ROSE
    assert tinted_at(0, WATCHING) == Tint.ROSE


def test_naming_the_seats_leaves_the_rest_of_a_layout_as_the_scene_laid_it_out() -> None:
    drawn = SEALED_SCENE.layout(SEATS, 0)
    named = Named(SEALED_SCENE, SEATED).layout(SEATS, 0)

    assert named.model_copy(update={"plaques": drawn.plaques}) == drawn


def test_a_plaque_goes_on_counting_what_it_counted_before_it_was_named() -> None:
    drawn = SEALED_SCENE.layout(SEATS, 0)
    named = Named(SEALED_SCENE, SEATED).layout(SEATS, 0)

    assert tuple(plaque.counts for plaque in named.plaques) == tuple(plaque.counts for plaque in drawn.plaques)


def _plaque_at(seat: int, observer: int | None) -> Plaque:
    """The plaque one seat takes on a layout drawn for that observer, with the gathering read onto it."""
    layout = Named(SEALED_SCENE, SEATED).layout(SEATS, observer)
    return next(plaque for plaque in layout.plaques if plaque.seat == seat)
