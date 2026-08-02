import pytest

from cardwork.effects.effects import SetFace
from cardwork.positions.position import Position
from cardwork.states.state import GameState


def faces(position: Position[GameState], zone_id: str) -> tuple[bool, ...]:
    return tuple(game_card.face_down for game_card in position.board.zone(zone_id).cards)


def test_set_face_turns_only_the_cards_it_addresses(position: Position[GameState]) -> None:
    effect: SetFace[GameState] = SetFace(zone="hand:0", indices=frozenset({0, 2}), face_down=False)

    turned = effect.apply(position)

    assert faces(turned, "hand:0") == (False, True, False)


def test_set_face_leaves_the_other_zones_as_they_lie(position: Position[GameState]) -> None:
    effect: SetFace[GameState] = SetFace(zone="hand:0", indices=frozenset({0}), face_down=False)

    turned = effect.apply(position)

    assert turned.board.zone("table") == position.board.zone("table")


def test_set_face_leaves_the_position_it_was_given_untouched(position: Position[GameState]) -> None:
    effect: SetFace[GameState] = SetFace(zone="hand:0", indices=frozenset({0}), face_down=False)

    effect.apply(position)

    assert faces(position, "hand:0") == (True, True, True)


def test_set_face_keeps_the_cards_themselves(position: Position[GameState]) -> None:
    effect: SetFace[GameState] = SetFace(zone="hand:0", indices=frozenset({0, 1, 2}), face_down=False)

    turned = effect.apply(position)

    assert [game_card.card for game_card in turned.board.zone("hand:0").cards] == [
        game_card.card for game_card in position.board.zone("hand:0").cards
    ]


def test_set_face_raises_on_an_unknown_zone(position: Position[GameState]) -> None:
    effect: SetFace[GameState] = SetFace(zone="nowhere", indices=frozenset({0}), face_down=True)

    with pytest.raises(KeyError):
        effect.apply(position)


def test_set_face_raises_on_an_index_past_the_end_of_the_zone(position: Position[GameState]) -> None:
    effect: SetFace[GameState] = SetFace(zone="hand:0", indices=frozenset({3}), face_down=True)

    with pytest.raises(KeyError):
        effect.apply(position)
