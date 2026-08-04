from collections.abc import Mapping
from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from cardwork.boards.board import Board
from cardwork.cards.cards import (
    ACE_OF_SPADES,
    KING_OF_HEARTS,
    QUEEN_OF_CLUBS,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardOrJoker, GameCard
from cardwork.effects.effects import MoveCards
from cardwork.positions.position import Position
from cardwork.states.state import GameState
from cardwork.zones.presets import PILE
from cardwork.zones.zone import Zone, ZoneId


@dataclass(frozen=True)
class LayoutCase:
    name: str
    effect: MoveCards[GameState]
    expected: Mapping[ZoneId, tuple[CardOrJoker, ...]]


@dataclass(frozen=True)
class FailureCase:
    name: str
    effect: MoveCards[GameState]
    error: type[Exception]


LAYOUT_CASES = (
    LayoutCase(
        name="appends to the target and closes the gap in the source",
        effect=MoveCards(source="hand:0", indices=frozenset({1}), target="table"),
        expected={"hand:0": (ACE_OF_SPADES, QUEEN_OF_CLUBS), "table": (TWO_OF_SPADES, KING_OF_HEARTS)},
    ),
    LayoutCase(
        name="lifts an unordered index set in source order",
        effect=MoveCards(source="hand:0", indices=frozenset({2, 0}), target="discard"),
        expected={"hand:0": (KING_OF_HEARTS,), "discard": (ACE_OF_SPADES, QUEEN_OF_CLUBS)},
    ),
    LayoutCase(
        name="inserts at the given index",
        effect=MoveCards(source="hand:0", indices=frozenset({0}), target="table", at=0),
        expected={"hand:0": (KING_OF_HEARTS, QUEEN_OF_CLUBS), "table": (ACE_OF_SPADES, TWO_OF_SPADES)},
    ),
    LayoutCase(
        name="fills an empty target",
        effect=MoveCards(source="table", indices=frozenset({0}), target="discard"),
        expected={"table": (), "discard": (TWO_OF_SPADES,)},
    ),
    LayoutCase(
        name="relocates within one zone",
        effect=MoveCards(source="hand:0", indices=frozenset({0}), target="hand:0", at=2),
        expected={"hand:0": (KING_OF_HEARTS, QUEEN_OF_CLUBS, ACE_OF_SPADES)},
    ),
)

FAILURE_CASES = (
    FailureCase(
        name="unknown source",
        effect=MoveCards(source="nowhere", indices=frozenset({0}), target="table"),
        error=KeyError,
    ),
    FailureCase(
        name="unknown target",
        effect=MoveCards(source="hand:0", indices=frozenset({0}), target="nowhere"),
        error=KeyError,
    ),
    FailureCase(
        name="index past the end of the source",
        effect=MoveCards(source="hand:0", indices=frozenset({3}), target="table"),
        error=KeyError,
    ),
    FailureCase(
        name="insertion index past the end of the target",
        effect=MoveCards(source="hand:0", indices=frozenset({0}), target="table", at=2),
        error=IndexError,
    ),
)


def cards_in(position: Position[GameState], zone_id: ZoneId) -> tuple[CardOrJoker, ...]:
    return tuple(game_card.card for game_card in position.board.zone(zone_id).cards)


@pytest.mark.parametrize("case", LAYOUT_CASES, ids=lambda case: case.name)
def test_move_cards_lays_the_zones_out_as_recorded(case: LayoutCase, position: Position[GameState]) -> None:
    moved = case.effect.apply(position)

    assert {zone_id: cards_in(moved, zone_id) for zone_id in case.expected} == dict(case.expected)


@pytest.mark.parametrize("case", FAILURE_CASES, ids=lambda case: case.name)
def test_move_cards_raises_on_an_address_the_board_cannot_honour(
    case: FailureCase, position: Position[GameState]
) -> None:
    with pytest.raises(case.error):
        case.effect.apply(position)


def test_move_cards_keeps_every_card_on_the_board(position: Position[GameState]) -> None:
    effect: MoveCards[GameState] = MoveCards(source="hand:0", indices=frozenset({0, 2}), target="discard")

    effect.apply(position).board.validate_board()


def test_move_cards_leaves_the_position_it_was_given_untouched(position: Position[GameState]) -> None:
    effect: MoveCards[GameState] = MoveCards(source="hand:0", indices=frozenset({0}), target="table")

    effect.apply(position)

    assert cards_in(position, "hand:0") == (ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS)
    assert cards_in(position, "table") == (TWO_OF_SPADES,)


def test_move_cards_turns_the_moved_cards_to_the_face_it_names(position: Position[GameState]) -> None:
    effect: MoveCards[GameState] = MoveCards(source="hand:0", indices=frozenset({0}), target="table", face_down=False)

    moved = effect.apply(position)

    assert moved.board.zone("table").cards[-1] == GameCard(card=ACE_OF_SPADES, face_down=False)


def test_move_cards_leaves_each_card_on_its_own_face_when_it_names_none() -> None:
    mixed = Zone(
        id="mixed",
        visibility=PILE,
        cards=(GameCard(card=ACE_OF_SPADES, face_down=True), GameCard(card=KING_OF_HEARTS, face_down=False)),
    )
    target = Zone(id="target", visibility=PILE)
    position: Position[GameState] = Position(
        board=Board(starting_deck=(ACE_OF_SPADES, KING_OF_HEARTS), zones={"mixed": mixed, "target": target}),
        state=GameState(phase="play"),
        players=1,
    )
    effect: MoveCards[GameState] = MoveCards(source="mixed", indices=frozenset({0, 1}), target="target")

    moved = effect.apply(position)

    assert moved.board.zone("target").cards == mixed.cards


@pytest.mark.parametrize("indices", [frozenset[int](), frozenset({-1})], ids=["empty", "negative"])
def test_move_cards_rejects_an_index_set_no_zone_can_answer(indices: frozenset[int]) -> None:
    with pytest.raises(ValidationError):
        MoveCards[GameState](source="hand:0", indices=indices, target="table")


def test_move_cards_rejects_a_negative_insertion_index() -> None:
    with pytest.raises(ValidationError):
        MoveCards[GameState](source="hand:0", indices=frozenset({0}), target="table", at=-1)
