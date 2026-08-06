from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from cardwork.combinations.poker import FLUSH, PAIR
from cardwork.combinations.policy import REGULAR_EVALUATION
from cardwork.combinations.ranking import Ranking
from cardwork.effects.effect import Effect
from cardwork.effects.effects import MoveCards, Reorder, SetFace, SetState
from cardwork.moves.actions import Declare, Play
from cardwork.moves.move import Move
from cardwork.states.state import GameState
from cardwork.transactions.transaction import Transaction


class BiddingState(GameState):
    trump: str
    highest_bid: int | None = None


class ContractState(GameState):
    """A cursor carrying the combinations the table settled on, which is what a bid contract comes to."""

    recognised: Ranking


@dataclass(frozen=True)
class EffectCase:
    name: str
    effect: Effect[GameState]


EFFECT_CASES = (
    EffectCase(
        name="move_cards keeps its optional fields",
        effect=MoveCards(source="hand:0", indices=frozenset({0, 2}), target="table", at=1, face_down=True),
    ),
    EffectCase(name="set_face", effect=SetFace(zone="hand:0", indices=frozenset({1}), face_down=False)),
    EffectCase(name="reorder", effect=Reorder(zone="deck", order=(2, 0, 1))),
    EffectCase(name="set_state", effect=SetState(state=GameState(phase="play", to_act=frozenset({0, 1})))),
)


@pytest.mark.parametrize("case", EFFECT_CASES, ids=lambda case: case.name)
def test_a_transaction_round_trips_every_field_of_the_effect_it_carries(case: EffectCase) -> None:
    transaction = Transaction[GameState](seq=4, move=None, effects=(case.effect,))

    restored = Transaction[GameState].model_validate_json(transaction.model_dump_json())

    assert restored == transaction


def test_a_transaction_round_trips_the_move_that_prompted_it() -> None:
    transaction = Transaction[GameState](
        seq=0,
        move=Move(player=1, action=Play(group="meld", indices=frozenset({0, 2}))),
        effects=(MoveCards(source="hand:1", indices=frozenset({0, 2}), target="meld"),),
    )

    restored = Transaction[GameState].model_validate_json(transaction.model_dump_json())

    assert restored == transaction
    assert restored.move is not None
    assert isinstance(restored.move.action, Play)


def test_a_transaction_round_trips_the_claim_a_seat_declared() -> None:
    transaction = Transaction[GameState](
        seq=3,
        move=Move(player=2, action=Declare(claim="three of a suit", indices=frozenset({0, 1, 3}))),
        effects=(SetState(state=GameState(phase="won", to_act=frozenset())),),
    )

    restored = Transaction[GameState].model_validate_json(transaction.model_dump_json())

    assert restored == transaction
    assert restored.move is not None
    assert isinstance(restored.move.action, Declare)
    assert restored.move.action.claim == "three of a suit"


def test_a_transaction_round_trips_a_game_s_own_state() -> None:
    transaction = Transaction[BiddingState](
        seq=1,
        move=None,
        effects=(SetState[BiddingState](state=BiddingState(phase="bid", trump="♦", highest_bid=5)),),
    )

    restored = Transaction[BiddingState].model_validate_json(transaction.model_dump_json())

    restored_effect = restored.effects[0]

    assert restored == transaction
    assert isinstance(restored_effect, SetState)
    assert restored_effect.state.highest_bid == 5


def test_a_transaction_round_trips_the_rules_a_table_settled_on() -> None:
    contract = ContractState(phase="play", recognised=Ranking(patterns=(PAIR, FLUSH), evaluation=REGULAR_EVALUATION))
    transaction = Transaction[ContractState](
        seq=2,
        move=None,
        effects=(SetState[ContractState](state=contract),),
    )

    restored = Transaction[ContractState].model_validate_json(transaction.model_dump_json())

    restored_effect = restored.effects[0]

    assert restored == transaction
    assert isinstance(restored_effect, SetState)
    assert restored_effect.state.recognised.patterns == (PAIR, FLUSH)


def test_a_transaction_rejects_an_effect_of_an_unrecorded_kind() -> None:
    with pytest.raises(ValidationError):
        Transaction[GameState].model_validate({"seq": 0, "move": None, "effects": [{"kind": "shuffle"}]})
