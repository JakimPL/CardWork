from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.decks.deck import Indices
from cardwork.moves.actions import (
    Action,
    AnyAction,
    Declare,
    Discard,
    Give,
    Pass,
    Play,
    Reject,
    Take,
    group_of,
    indices_of,
    kind_of,
)
from cardwork.moves.move import Move
from tests.cases import Case, descriptions

ACTIONS = (
    Pass(),
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


@dataclass(frozen=True)
class IndicesCase(Case):
    action: AnyAction
    indices: Indices


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
    GroupCase(
        description="a pass names its word alone",
        action=Pass(),
        group=None,
    ),
)

POSITIONS: Final[tuple[IndicesCase, ...]] = (
    IndicesCase(
        description="a play names the cards it is made of",
        action=Play(group="meld", indices=frozenset({0, 2})),
        indices=frozenset({0, 2}),
    ),
    IndicesCase(
        description="a declaration made of a whole zone names no position of it",
        action=Declare(claim="a winning hand", indices=frozenset()),
        indices=frozenset(),
    ),
    IndicesCase(
        description="a pass names no card at all",
        action=Pass(),
        indices=frozenset(),
    ),
)


@pytest.mark.parametrize("case", GROUPS, ids=descriptions(GROUPS))
def test_the_group_an_intent_names_is_read_off_the_action(case: GroupCase) -> None:
    assert group_of(case.action) == case.group


@pytest.mark.parametrize("case", POSITIONS, ids=descriptions(POSITIONS))
def test_the_positions_an_intent_names_are_read_off_the_action(case: IndicesCase) -> None:
    assert indices_of(case.action) == case.indices


@pytest.mark.parametrize("action", ACTIONS, ids=lambda action: action.kind)
def test_the_word_read_off_a_class_is_the_word_an_action_of_it_carries(action: AnyAction) -> None:
    assert kind_of(type(action)) == action.kind


def test_reading_the_word_off_a_class_that_states_none_is_refused() -> None:
    with pytest.raises(TypeError, match="where the word naming a kind of intent belongs"):
        kind_of(Action)


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
