from http import HTTPStatus
from random import Random
from typing import Final

from cardgames.passing.game import PassingGame
from cardgames.passing.rules import HAND_ON_TURN, HAND_SIZE, NOTHING
from cardgames.passing.state import PassingPhase, PassingState
from cardgames.passing.zones import PILE, STACK, hand_of
from cardserver.sessions import TableSession
from cardwork.decks.deck import Deck
from cardwork.decks.standard import standard_decks
from cardwork.moves.actions import Give, Take
from cardwork.moves.move import Move
from cardwork.rounds.seating import next_seat

from .conftest import DEAL, MOVES, VIEW, command, credentials, served

SEATS: Final[int] = 3
SEED: Final[int] = 20260806
DECK: Final[Deck] = standard_decks(1, black_jokers=1, red_jokers=1)
FIRST_CARD: Final[frozenset[int]] = frozenset({0})
FIRST_ROUND: Final[int] = 1
ONE_CARD: Final[int] = 1


def a_passing_table() -> PassingGame:
    """A three-seat match over one jokered deck, which is the game as `cardgames.passing` plays it."""
    return PassingGame(players=SEATS, deck=DECK, rng=Random(SEED))


def turn_of(session: TableSession[PassingState]) -> int:
    """The seat the round in play stands with, read from the table the way any observer reads it.

    Raises:
        ValueError: when the turn stands with several seats or with none, which a round in play never reaches.
    """
    seat = session.view(observer=None).state.current
    if seat is None:
        raise ValueError(f"One seat holds the turn, and the table at sequence {session.head} names another number")

    return seat


def exchange(seat: int) -> Move:
    """The seat on turn giving up the first card it reads for the top of the pile."""
    return Move(player=seat, action=Take(group=PILE, indices=FIRST_CARD))


def pass_on(seat: int) -> Move:
    """The seat on turn handing its first card to the seat next round the table."""
    return Move(player=seat, action=Give(target_player=next_seat(seat, SEATS), indices=FIRST_CARD))


async def test_a_served_round_carries_the_cursor_the_game_declared_out_to_the_wire() -> None:
    async with served(a_passing_table(), SEATS) as (client, session):
        leading = turn_of(session)

        response = await client.get(VIEW, headers=credentials(0))

    assert response.status_code == HTTPStatus.OK
    state = response.json()["state"]
    assert state["phase"] == PassingPhase.PASSING
    assert state["swapped"] is False
    assert state["winner"] is None
    assert state["round_number"] == FIRST_ROUND
    assert state["leader"] == leading
    assert state["to_act"] == [leading]
    assert state["points"] == [NOTHING] * SEATS


async def test_the_seat_on_turn_exchanges_with_the_pile_over_the_wire() -> None:
    async with served(a_passing_table(), SEATS) as (client, session):
        turn = turn_of(session)

        accepted = await client.post(MOVES, json=command(exchange(turn), DEAL, "exchange"), headers=credentials(turn))
        view = await client.get(VIEW, headers=credentials(turn))

    assert accepted.status_code == HTTPStatus.OK
    assert accepted.json() == {"seq": DEAL}
    zones = view.json()["zones"]
    assert view.json()["state"]["swapped"] is True
    assert len(zones[hand_of(turn)]["cards"]) == HAND_ON_TURN
    assert all(card is not None for card in zones[hand_of(turn)]["cards"])
    assert len(zones[STACK]["cards"]) == ONE_CARD
    assert all(card is not None for card in zones[STACK]["cards"])


async def test_the_pass_hands_the_turn_and_the_fourth_card_to_the_next_seat_over_the_wire() -> None:
    async with served(a_passing_table(), SEATS) as (client, session):
        turn = turn_of(session)

        await client.post(MOVES, json=command(pass_on(turn), DEAL, "pass"), headers=credentials(turn))
        view = await client.get(VIEW)

    following = next_seat(turn, SEATS)
    state = view.json()["state"]
    zones = view.json()["zones"]
    assert state["to_act"] == [following]
    assert state["swapped"] is False
    assert zones[hand_of(following)]["cards"] == [None] * HAND_ON_TURN
    assert zones[hand_of(turn)]["cards"] == [None] * HAND_SIZE


async def test_a_second_exchange_in_one_turn_is_refused_over_the_wire() -> None:
    async with served(a_passing_table(), SEATS) as (client, session):
        turn = turn_of(session)
        await client.post(MOVES, json=command(exchange(turn), DEAL, "first"), headers=credentials(turn))

        response = await client.post(
            MOVES,
            json=command(exchange(turn), session.head, "second"),
            headers=credentials(turn),
        )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["error"] == "IllegalMove"
