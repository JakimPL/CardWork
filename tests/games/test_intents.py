from dataclasses import dataclass
from random import Random
from typing import ClassVar, Final

import pytest

from cardwork.exceptions import IllegalMove
from cardwork.games.intents import Intents
from cardwork.moves.actions import (
    AnyAction,
    Declare,
    Discard,
    Give,
    Pass,
    Play,
    Reject,
    Take,
)
from cardwork.moves.kind import ActionKind
from cardwork.moves.move import Move
from tests.cases import Case, descriptions

from .conftest import SEED
from .demo import DECK, SEATS, BareGame, DiscardGame

SEAT: Final[int] = 1
FIRST_CARD: Final[frozenset[int]] = frozenset({0})
LAID: Final[Play] = Play(group="discard", indices=FIRST_CARD)
HANDED: Final[Give] = Give(target_player=0, indices=FIRST_CARD)
CLAIMED: Final[Declare] = Declare(claim="a winning hand", indices=frozenset())
GIVEN_UP: Final[Pass] = Pass()


class GivingGame(BareGame):
    """A game played with one intent, whose `validate` reads a move for nothing at all.

    Every rule of this one admits whatever reaches it, so a refusal it answers with came from the vocabulary
    the engine holds a move to before the rules see it.
    """

    intents: ClassVar[Intents[Give]] = Intents(Give)


@dataclass(frozen=True)
class ReadingCase(Case):
    intents: Intents[AnyAction]
    action: AnyAction


@dataclass(frozen=True)
class RefusalCase(Case):
    intents: Intents[AnyAction]
    action: AnyAction
    refusal: str


READINGS: Final[tuple[ReadingCase, ...]] = (
    ReadingCase(
        description="a game played with one intent reads the intent it is played with",
        intents=Intents(Play),
        action=LAID,
    ),
    ReadingCase(
        description="a game played with two reads either of them",
        intents=Intents(Take, Give),
        action=HANDED,
    ),
    ReadingCase(
        description="a game played with the intent naming no card reads a pass",
        intents=Intents(Play, Pass),
        action=GIVEN_UP,
    ),
)

REFUSALS: Final[tuple[RefusalCase, ...]] = (
    RefusalCase(
        description="a vocabulary of one names the intent it holds",
        intents=Intents(Play),
        action=HANDED,
        refusal="Seat 1 makes a play, and offered a give",
    ),
    RefusalCase(
        description="a vocabulary of two names both of them",
        intents=Intents(Take, Give),
        action=LAID,
        refusal="Seat 1 makes a take or a give, and offered a play",
    ),
    RefusalCase(
        description="a vocabulary of three names each of them in turn",
        intents=Intents(Play, Take, Give),
        action=CLAIMED,
        refusal="Seat 1 makes a play, a take or a give, and offered a declare",
    ),
)


@pytest.mark.parametrize("case", READINGS, ids=descriptions(READINGS))
def test_a_move_reads_back_as_the_action_it_carries(case: ReadingCase) -> None:
    assert case.intents.read(Move(player=SEAT, action=case.action)) is case.action


@pytest.mark.parametrize("case", REFUSALS, ids=descriptions(REFUSALS))
def test_an_intent_left_out_is_refused_by_the_words_it_stands_beside(case: RefusalCase) -> None:
    with pytest.raises(IllegalMove) as refused:
        case.intents.read(Move(player=SEAT, action=case.action))

    assert refused.value.reason == case.refusal


def test_a_vocabulary_reads_the_words_of_the_actions_it_holds() -> None:
    assert Intents(Discard, Reject).kinds == (ActionKind.DISCARD, ActionKind.REJECT)


def test_a_vocabulary_holds_the_actions_in_the_order_they_were_named() -> None:
    assert Intents(Give, Play).accepted == (Give, Play)


def test_a_vocabulary_naming_no_action_is_refused() -> None:
    with pytest.raises(ValueError, match="one intent at the least"):
        Intents()


def test_a_game_states_the_vocabulary_it_is_played_with() -> None:
    assert DiscardGame.intents.accepted == (Play,)


def test_a_game_states_no_vocabulary_by_leaving_the_declaration_at_none() -> None:
    assert BareGame.intents is None


def test_an_intent_a_game_is_played_without_is_refused_before_its_rules_read_the_move() -> None:
    game = GivingGame(players=SEATS, deck=DECK, rng=Random(SEED))

    with pytest.raises(IllegalMove, match="makes a give, and offered a play"):
        game.submit(Move(player=SEAT, action=LAID), base_seq=game.head)


def test_an_intent_a_game_is_played_with_reaches_its_rules() -> None:
    game = GivingGame(players=SEATS, deck=DECK, rng=Random(SEED))

    committed = game.submit(Move(player=SEAT, action=HANDED), base_seq=game.head)

    assert committed.move is not None
    assert committed.move.action == HANDED


@pytest.mark.parametrize("action", (CLAIMED, GIVEN_UP), ids=lambda action: str(action.kind))
def test_a_game_stating_no_vocabulary_reads_a_move_of_any_kind(action: AnyAction) -> None:
    game = BareGame(players=SEATS, deck=DECK, rng=Random(SEED))

    committed = game.submit(Move(player=SEAT, action=action), base_seq=game.head)

    assert committed.move is not None
    assert committed.move.action == action
