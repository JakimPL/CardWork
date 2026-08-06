import pytest

from cardwork.presentation.readout import Readout
from cardwork.presentation.scope import Scope
from cardwork.states.state import GameState


class TrumpState(GameState):
    """A cursor of a game's own, declaring a field the engine knows nothing of."""

    trump: str | None = None


def test_a_readout_names_a_field_the_shared_cursor_declares() -> None:
    assert Readout.of(GameState, "to_act", "To act", scope=Scope.TABLE).field == "to_act"


def test_a_readout_names_a_field_a_game_declares_for_itself() -> None:
    assert Readout.of(TrumpState, "trump", "Trump", scope=Scope.TABLE).field == "trump"


def test_a_readout_carries_the_word_and_the_reach_it_was_given() -> None:
    standing = Readout.of(GameState, "points", "Points", scope=Scope.SEAT)

    assert (standing.label, standing.scope) == ("Points", Scope.SEAT)


def test_a_readout_of_a_field_no_state_declares_is_refused() -> None:
    with pytest.raises(ValueError, match="GameState declares no field 'trump'"):
        Readout.of(GameState, "trump", "Trump", scope=Scope.TABLE)


def test_a_readout_of_a_field_another_game_declares_is_refused() -> None:
    with pytest.raises(ValueError, match="TrumpState declares no field 'bid'"):
        Readout.of(TrumpState, "bid", "Bid", scope=Scope.TABLE)
