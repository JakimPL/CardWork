import pytest
from pydantic import ValidationError

from cardwork.states.state import GameState


class BiddingState(GameState):
    trump: str
    highest_bid: int | None = None


def test_current_names_the_single_seat_owing_an_action() -> None:
    assert GameState(phase="play", to_act=frozenset({2})).current == 2


def test_current_stays_open_while_several_seats_owe_an_action() -> None:
    assert GameState(phase="arrange", to_act=frozenset({0, 1, 2})).current is None


def test_current_stays_open_once_the_round_has_closed() -> None:
    assert GameState(phase="reveal").current is None


def test_state_rejects_attribute_assignment() -> None:
    state = GameState(phase="play")

    with pytest.raises(ValueError):
        state.phase = "reveal"


def test_points_are_stored_as_an_immutable_run() -> None:
    state = GameState(phase="score", points=[3, 5])

    assert state.points == (3, 5)


def test_with_changes_carries_the_untouched_fields_forward() -> None:
    state = BiddingState(phase="bid", to_act=frozenset({0, 1}), trump="♠")

    advanced = state.with_changes(to_act=frozenset({1}))

    assert advanced == BiddingState(phase="bid", to_act=frozenset({1}), trump="♠")


def test_with_changes_keeps_the_game_s_own_state_type() -> None:
    state = BiddingState(phase="bid", trump="♠")

    assert isinstance(state.with_changes(highest_bid=4), BiddingState)


def test_with_changes_leaves_the_state_it_was_given_untouched() -> None:
    state = BiddingState(phase="bid", trump="♠")

    state.with_changes(phase="play")

    assert state.phase == "bid"


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"highest_bid": "three"}, id="a value outside the declared type"),
        pytest.param({"to_act": {"north"}}, id="a seat that is no number"),
        pytest.param({"suit": "♠"}, id="a field the state does not declare"),
    ],
)
def test_with_changes_rejects_what_model_copy_would_have_written(changes: dict[str, object]) -> None:
    state = BiddingState(phase="bid", trump="♠")

    with pytest.raises(ValidationError):
        state.with_changes(**changes)
