from typing import Final

from fastapi import FastAPI

SCHEMAS: Final[str] = "schemas"
LAYOUT: Final[str] = "Layout"
GENERATED: Final[tuple[str, ...]] = ("Layout", "Slot", "Gesture", "Plaque", "Readout", "Tally", "Move", "MoveRequest")
PROJECTIONS: Final[tuple[str, ...]] = ("PositionView", "EventView")


def published(app: FastAPI) -> dict[str, dict[str, object]]:
    """Every shape the document an application publishes states, filed under the name it states it by."""
    components: dict[str, dict[str, dict[str, object]]] = app.openapi()["components"]
    return components[SCHEMAS]


def test_the_document_states_the_arrangement_a_client_draws_the_table_from(app: FastAPI) -> None:
    """The one answer standing apart from a game's own state, which is what a client generates its types from.

    A layout is the same shape whichever game is in service, so it reaches the document and an interface reads
    its own vocabulary out of it rather than restating the fields a game laid out.
    """
    assert set(GENERATED) <= set(published(app))


def test_the_document_leaves_the_answers_carrying_a_game_state_to_the_client_to_state(app: FastAPI) -> None:
    """A view and an event are generic in the state a game declares, which leaves a schema nothing to build on.

    An interface mirrors those two by hand for exactly this reason, and the fields a particular game adds to
    its cursor arrive inside them as the game itself declared them.
    """
    assert not set(PROJECTIONS) & set(published(app))


def test_a_layout_the_document_states_holds_every_field_an_interface_draws_it_by(app: FastAPI) -> None:
    laid_out = published(app)[LAYOUT]

    assert set(laid_out["required"]) == {
        "title",
        "observer",
        "players",
        "slots",
        "gestures",
        "plaques",
        "readouts",
        "phases",
    }
