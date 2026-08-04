from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.moves.actions import (
    AnyAction,
    Declare,
    Discard,
    Give,
    Play,
    Reject,
    Take,
    group_of,
)
from cardwork.moves.move import Move
from tests.cases import Case, descriptions

ACTIONS = (
    Play(group="meld", indices=frozenset({0, 2})),
    Take(group="discard", indices=frozenset({0})),
    Give(target_player=2, indices=frozenset({1, 3})),
    Reject(indices=frozenset({4})),
    Discard(group="hand", indices=frozenset({0})),
    Declare(claim="three of a rank", indices=frozenset({0, 1, 3})),
)


@dataclass(frozen=True)
class GroupCase(Case):
    action: AnyAction
    group: str | None


GROUPS: Final[tuple[GroupCase, ...]] = (
    GroupCase(
        description="a play names the group it is made in",
        action=Play(group="meld", indices=frozenset({0})),
        group="meld",
    ),
    GroupCase(
        description="an exchange names the group it is with",
        action=Take(group="discard", indices=frozenset({0})),
        group="discard",
    ),
    GroupCase(
        description="a discard names the group it goes to",
        action=Discard(group="hand", indices=frozenset({0})),
        group="hand",
    ),
    GroupCase(
        description="a pass names a seat in place of a group",
        action=Give(target_player=2, indices=frozenset({0})),
        group=None,
    ),
    GroupCase(
        description="a rejection names its cards alone",
        action=Reject(indices=frozenset({0})),
        group=None,
    ),
    GroupCase(
        description="a declaration names a claim in place of a group",
        action=Declare(claim="three of a rank", indices=frozenset({0})),
        group=None,
    ),
)


@pytest.mark.parametrize("case", GROUPS, ids=descriptions(GROUPS))
def test_the_group_an_intent_names_is_read_off_the_action(case: GroupCase) -> None:
    assert group_of(case.action) == case.group


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
