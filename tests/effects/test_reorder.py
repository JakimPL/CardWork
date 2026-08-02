from dataclasses import dataclass
from random import Random

import pytest

from cardwork.cards.cards import ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS
from cardwork.cards.game import CardOrJoker
from cardwork.decks.draw import permutation
from cardwork.effects.effects import Reorder
from cardwork.positions.position import Position
from cardwork.states.state import GameState


@dataclass(frozen=True)
class OrderCase:
    name: str
    order: tuple[int, ...]
    expected: tuple[CardOrJoker, ...]


ORDER_CASES = (
    OrderCase(name="identity", order=(0, 1, 2), expected=(ACE_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_CLUBS)),
    OrderCase(name="reversal", order=(2, 1, 0), expected=(QUEEN_OF_CLUBS, KING_OF_HEARTS, ACE_OF_SPADES)),
    OrderCase(name="rotation", order=(1, 2, 0), expected=(KING_OF_HEARTS, QUEEN_OF_CLUBS, ACE_OF_SPADES)),
)

REJECTED_ORDERS = (
    pytest.param((0, 1), id="too short"),
    pytest.param((0, 1, 2, 3), id="too long"),
    pytest.param((0, 0, 1), id="repeated position"),
    pytest.param((0, 1, 3), id="position past the end"),
)


@pytest.mark.parametrize("case", ORDER_CASES, ids=lambda case: case.name)
def test_reorder_lays_the_zone_out_in_the_recorded_order(case: OrderCase, position: Position[GameState]) -> None:
    effect: Reorder[GameState] = Reorder(zone="hand:0", order=case.order)

    reordered = effect.apply(position)

    assert tuple(game_card.card for game_card in reordered.board.zone("hand:0").cards) == case.expected


@pytest.mark.parametrize("order", REJECTED_ORDERS)
def test_reorder_raises_on_an_order_that_is_no_permutation(
    order: tuple[int, ...], position: Position[GameState]
) -> None:
    effect: Reorder[GameState] = Reorder(zone="hand:0", order=order)

    with pytest.raises(ValueError, match="not a permutation"):
        effect.apply(position)


def test_reorder_accepts_the_empty_order_of_an_empty_zone(position: Position[GameState]) -> None:
    effect: Reorder[GameState] = Reorder(zone="discard", order=())

    assert effect.apply(position).board.zone("discard").cards == ()


def test_reorder_raises_on_an_unknown_zone(position: Position[GameState]) -> None:
    effect: Reorder[GameState] = Reorder(zone="nowhere", order=())

    with pytest.raises(KeyError):
        effect.apply(position)


def test_reorder_replays_a_drawn_shuffle_from_the_record_alone(position: Position[GameState], rng: Random) -> None:
    order = permutation(len(position.board.zone("hand:0").cards), rng)
    drawn: Reorder[GameState] = Reorder(zone="hand:0", order=order)
    recorded = Reorder[GameState].model_validate_json(drawn.model_dump_json())

    assert recorded.apply(position) == drawn.apply(position)


def test_reorder_keeps_every_card_on_the_board(position: Position[GameState]) -> None:
    effect: Reorder[GameState] = Reorder(zone="hand:0", order=(2, 0, 1))

    effect.apply(position).board.validate_board()
