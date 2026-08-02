from cardwork.effects.effect import Effect
from cardwork.effects.effects import MoveCards, SetState
from cardwork.effects.fold import fold
from cardwork.positions.position import Position
from cardwork.states.state import GameState


def test_fold_threads_each_result_into_the_next(position: Position[GameState]) -> None:
    effects: tuple[Effect[GameState], ...] = (
        MoveCards(source="hand:0", indices=frozenset({0}), target="discard"),
        MoveCards(source="hand:0", indices=frozenset({0}), target="discard"),
    )

    folded = fold(effects, position)

    assert len(folded.board.zone("discard").cards) == 2
    assert len(folded.board.zone("hand:0").cards) == 1


def test_fold_applies_effects_of_different_kinds_in_order(position: Position[GameState]) -> None:
    effects: tuple[Effect[GameState], ...] = (
        MoveCards(source="hand:0", indices=frozenset({0}), target="table", face_down=False),
        SetState(state=GameState(phase="score")),
    )

    folded = fold(effects, position)

    assert folded.state.phase == "score"
    assert folded.board.zone("table").cards[-1].face_down is False


def test_fold_of_nothing_returns_the_position_it_was_given(position: Position[GameState]) -> None:
    assert fold((), position) == position
