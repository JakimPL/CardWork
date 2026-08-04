from http import HTTPStatus
from random import Random
from typing import Final

from httpx import AsyncClient

from cardgames.backend.showdown.game import ShowdownGame
from cardgames.backend.showdown.rules import (
    BLIND_SIZE,
    HAND_SIZE,
    NOTHING,
    ONE_CARD,
    TURNS,
)
from cardgames.backend.showdown.state import ShowdownState
from cardgames.backend.showdown.zones import (
    DISCARD,
    Holding,
    blind_of,
    hand_of,
    tray_of,
)
from cardgames.frontend.showdown.layout import SHOWDOWN_SCENE
from cardserver.sessions import TableSession
from cardwork.decks.deck import Deck
from cardwork.decks.standard import standard_deck
from cardwork.moves.actions import Play
from cardwork.moves.move import Move
from cardwork.rounds.conclusion import ONE_ROUND, Conclusion
from cardwork.rounds.state import MatchPhase

from .conftest import DEAL, MOVES, VIEW, command, credentials, served

SEATS: Final[int] = 3
SEED: Final[int] = 20260807
DECK: Final[Deck] = standard_deck()
FIRST_CARD: Final[frozenset[int]] = frozenset({0})
SECOND_TURN: Final[int] = 2
STILL_TO_COMMIT: Final[list[int]] = [1, 2]


def a_showdown_table() -> ShowdownGame:
    """A three-seat match over one round, which is the game as `cardgames.backend.showdown` plays it."""
    return ShowdownGame(players=SEATS, deck=DECK, conclusion=Conclusion(rounds=ONE_ROUND), rng=Random(SEED))


def commitment(seat: int, holding: Holding) -> Move:
    """One seat committing the first card of that holding to the turn."""
    return Move(player=seat, action=Play(group=holding, indices=FIRST_CARD))


def a_holding_of(session: TableSession[ShowdownState], seat: int) -> Holding:
    """The holding a seat still has a card in, which is its hand for as long as that holds one."""
    return Holding.HAND if session.view(observer=None).zones[hand_of(seat)].cards else Holding.BLIND


async def commit_the_turn(client: AsyncClient, session: TableSession[ShowdownState], turn: int) -> None:
    """Every seat commits a card, each command pinned to the sequence the one before it left the table at."""
    for seat in range(SEATS):
        await client.post(
            MOVES,
            json=command(commitment(seat, a_holding_of(session, seat)), session.head, f"turn-{turn}-seat-{seat}"),
            headers=credentials(seat),
        )


async def test_a_seat_reads_the_five_it_holds_while_the_five_it_plays_blind_read_to_nobody() -> None:
    async with served(a_showdown_table(), SHOWDOWN_SCENE) as (client, _):
        own = await client.get(VIEW, headers=credentials(0))
        spectator = await client.get(VIEW)

    assert all(card is not None for card in own.json()["zones"][hand_of(0)]["cards"])
    assert own.json()["zones"][blind_of(0)]["cards"] == [None] * BLIND_SIZE
    assert spectator.json()["zones"][hand_of(0)]["cards"] == [None] * HAND_SIZE
    assert spectator.json()["zones"][blind_of(0)]["cards"] == [None] * BLIND_SIZE


async def test_a_commitment_is_sealed_from_the_whole_table_while_the_turn_stands_open() -> None:
    async with served(a_showdown_table(), SHOWDOWN_SCENE) as (client, _):
        accepted = await client.post(
            MOVES,
            json=command(commitment(0, Holding.HAND), DEAL, "commitment"),
            headers=credentials(0),
        )
        own = await client.get(VIEW, headers=credentials(0))
        spectator = await client.get(VIEW)

    assert accepted.status_code == HTTPStatus.OK
    assert own.json()["zones"][tray_of(0)]["cards"] == [None] * ONE_CARD
    assert spectator.json()["zones"][tray_of(0)]["cards"] == [None] * ONE_CARD
    assert len(own.json()["zones"][hand_of(0)]["cards"]) == HAND_SIZE - ONE_CARD
    assert sorted(own.json()["state"]["to_act"]) == STILL_TO_COMMIT


async def test_a_second_commitment_in_one_turn_is_refused_over_the_wire() -> None:
    async with served(a_showdown_table(), SHOWDOWN_SCENE) as (client, session):
        await client.post(MOVES, json=command(commitment(0, Holding.HAND), DEAL, "first"), headers=credentials(0))

        response = await client.post(
            MOVES,
            json=command(commitment(0, Holding.BLIND), session.head, "second"),
            headers=credentials(0),
        )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["error"] == "NotYourTurn"


async def test_a_turn_every_seat_has_committed_to_turns_over_once_the_window_has_passed() -> None:
    async with served(a_showdown_table(), SHOWDOWN_SCENE) as (client, session):
        await commit_the_turn(client, session, turn=DEAL)

        await session.drain()

        view = await client.get(VIEW, headers=credentials(0))

    state = view.json()["state"]
    zones = view.json()["zones"]
    assert len(zones[DISCARD]["cards"]) == SEATS
    assert all(card is not None for card in zones[DISCARD]["cards"])
    assert all(zones[tray_of(seat)]["cards"] == [] for seat in range(SEATS))
    assert state["turn_number"] == SECOND_TURN
    assert state["rounds"] == ONE_ROUND
    assert sum(state["round_points"]) > NOTHING
    assert sorted(state["to_act"]) == list(range(SEATS))


async def test_a_match_played_out_over_the_wire_comes_to_rest_on_the_standing_it_scored() -> None:
    async with served(a_showdown_table(), SHOWDOWN_SCENE) as (client, session):
        for turn in range(TURNS):
            await commit_the_turn(client, session, turn)
            await session.drain()

        view = await client.get(VIEW)

    state = view.json()["state"]
    assert state["phase"] == MatchPhase.MATCH_OVER
    assert state["round_number"] == ONE_ROUND
    assert state["to_act"] == []
    assert sum(state["points"]) > NOTHING
    assert len(view.json()["zones"][DISCARD]["cards"]) == TURNS * SEATS
