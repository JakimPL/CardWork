import pytest
from pydantic import ValidationError

from cardwork.moves.actions import AnyAction, Declare, Discard, Give, Play, Reject, Take
from cardwork.moves.move import Move

ACTIONS = (
    Play(group="meld", indices=frozenset({0, 2})),
    Take(group="discard", indices=frozenset({0})),
    Give(target_player=2, indices=frozenset({1, 3})),
    Reject(indices=frozenset({4})),
    Discard(group="hand", indices=frozenset({0})),
    Declare(claim="three of a rank", indices=frozenset({0, 1, 3})),
)


@pytest.mark.parametrize("action", ACTIONS, ids=lambda action: action.kind)
def test_a_move_round_trips_every_field_of_the_action_it_carries(action: AnyAction) -> None:
    move = Move(player=1, action=action)

    restored = Move.model_validate_json(move.model_dump_json())

    assert restored == move
    assert type(restored.action) is type(action)


def test_a_declaration_carries_a_claim_made_of_no_named_card() -> None:
    move = Move(player=1, action=Declare(claim="a winning hand", indices=frozenset()))

    restored = Move.model_validate_json(move.model_dump_json())

    assert restored == move


def test_a_move_rejects_an_action_of_an_unrecorded_kind() -> None:
    with pytest.raises(ValidationError):
        Move.model_validate({"player": 0, "action": {"kind": "bid", "amount": 3}})


def test_a_move_rejects_a_seat_below_the_table() -> None:
    with pytest.raises(ValidationError):
        Move(player=-1, action=Reject(indices=frozenset({0})))


def test_give_rejects_a_recipient_below_the_table() -> None:
    with pytest.raises(ValidationError):
        Give(target_player=-1, indices=frozenset({0}))
