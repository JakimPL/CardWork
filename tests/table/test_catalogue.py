from http import HTTPStatus

import pytest

from cardtable.catalogue import (
    a_passing_match,
    a_shedding_match,
    a_showdown_match,
    opened,
)
from cardtable.games import GameName
from cardwork.presentation.layout import Layout
from cardwork.rounds.conclusion import Conclusion
from tests.cases import descriptions

from .config import GLYPHS
from .tables import (
    CASES,
    LAYOUT,
    PLAYERS,
    ROUNDS,
    SETTINGS,
    VIEW,
    HostCase,
    a_seat_to_act,
    credentials,
    playing,
    submit,
)

SEATED = 1
A_LEAD = 2
WATCHING: int | None = None


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_seat_is_served_the_layout_the_game_states_for_it(case: HostCase) -> None:
    async with playing(case.game) as (client, hosted):
        response = await client.get(LAYOUT, headers=credentials(hosted, SEATED))

    assert Layout.model_validate(response.json()) == case.scene.layout(PLAYERS, SEATED)


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_spectator_is_served_the_layout_the_game_states_for_one(case: HostCase) -> None:
    async with playing(case.game) as (client, _):
        response = await client.get(LAYOUT)

    assert Layout.model_validate(response.json()) == case.scene.layout(PLAYERS, WATCHING)


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_table_opens_dealt_and_settled(case: HostCase) -> None:
    async with playing(case.game) as (client, hosted):
        response = await client.get(VIEW, headers=credentials(hosted, SEATED))

    assert response.json()["seq"] > 0


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_token_speaks_for_the_seat_it_was_issued_for(case: HostCase) -> None:
    async with playing(case.game) as (client, hosted):
        served = [
            (await client.get(VIEW, headers=credentials(hosted, seat))).json()["observer"] for seat in range(PLAYERS)
        ]

    assert served == list(range(PLAYERS))


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_move_a_seat_is_offered_lands_through_the_host(case: HostCase) -> None:
    async with playing(case.game) as (client, hosted):
        seat, move, base_seq = await a_seat_to_act(client, hosted)

        status = await submit(client, hosted, seat, move, base_seq)
        after = (await client.get(VIEW, headers=credentials(hosted, seat))).json()

    assert status == HTTPStatus.OK
    assert after["seq"] > base_seq


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_token_makes_no_move_for_another_seat(case: HostCase) -> None:
    async with playing(case.game) as (client, hosted):
        seat, move, base_seq = await a_seat_to_act(client, hosted)
        impostor = (seat + 1) % PLAYERS

        status = await submit(client, hosted, impostor, move, base_seq)

    assert status == HTTPStatus.FORBIDDEN


def test_a_match_of_passing_is_dealt_for_the_seats_asked_for() -> None:
    assert a_passing_match(SETTINGS).players == PLAYERS


def test_a_match_of_showdown_runs_the_rounds_asked_for() -> None:
    assert a_showdown_match(SETTINGS).position.state.rounds == ROUNDS


def test_a_match_of_shedding_runs_the_rounds_asked_for() -> None:
    assert a_shedding_match(SETTINGS).position.state.rounds == ROUNDS


def test_every_game_a_host_opens_runs_to_the_ending_its_table_states() -> None:
    """One conclusion opens any of them, which is what a match length stated by the table rather than the rules buys."""
    settings = SETTINGS.model_copy(update={"conclusion": Conclusion(lead=A_LEAD)})

    for match in (a_passing_match(settings), a_showdown_match(settings), a_shedding_match(settings)):
        assert match.position.state.lead == A_LEAD
        assert match.position.state.rounds is None


def test_a_game_is_opened_under_the_name_the_settings_give_the_table() -> None:
    assert opened(GameName.PASSING, SETTINGS, GLYPHS).table == SETTINGS.name
