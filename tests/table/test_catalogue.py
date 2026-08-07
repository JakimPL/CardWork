from http import HTTPStatus

import pytest

from cardserver.naming import Named
from cardserver.registry import TableRegistry
from cardtable.catalogue import (
    TWO_DECKS,
    Deals,
    a_climbing_match,
    a_passing_match,
    a_shedding_match,
    a_showdown_match,
    opened,
)
from cardtable.games import GameName
from cardwork.decks.standard import ONE_DECK
from cardwork.exceptions import GameValidationError
from cardwork.presentation.layout import Layout
from cardwork.rounds.conclusion import Conclusion
from tests.cases import descriptions

from .config import ADVANCED, GLYPHS
from .tables import (
    CASES,
    CHOICE,
    LAYOUT,
    NAMES,
    NO_GRACE,
    PLAYERS,
    ROUNDS,
    SEED,
    SETTINGS,
    VIEW,
    HostCase,
    a_seat_to_act,
    a_seated_company,
    playing,
    settled,
    submit,
)

SEATED = 1
A_LEAD = 2
WATCHING: int | None = None
SEATS_NO_GAME_HOLDS = 9
FIRST_SEAT = 0


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_seat_is_served_the_layout_the_game_states_for_it(case: HostCase) -> None:
    async with playing(case.game) as dealt:
        response = await dealt.client.get(LAYOUT, headers=dealt.credentials(SEATED))

    named = Named(case.scene, a_seated_company(PLAYERS))
    assert Layout.model_validate(response.json()) == named.layout(PLAYERS, SEATED)


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_spectator_is_served_the_layout_the_game_states_for_one(case: HostCase) -> None:
    async with playing(case.game) as dealt:
        response = await dealt.client.get(LAYOUT)

    named = Named(case.scene, a_seated_company(PLAYERS))
    assert Layout.model_validate(response.json()) == named.layout(PLAYERS, WATCHING)


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_every_seat_of_a_dealt_table_is_read_by_the_name_its_guest_arrived_under(case: HostCase) -> None:
    """The whole of what a gathering leaves on the felt: the company reads at the table it settled."""
    async with playing(case.game) as dealt:
        response = await dealt.client.get(LAYOUT, headers=dealt.credentials(SEATED))

    plaques = Layout.model_validate(response.json()).plaques
    assert tuple(plaque.name for plaque in plaques) == NAMES[:PLAYERS]


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_table_opens_dealt_and_settled(case: HostCase) -> None:
    async with playing(case.game) as dealt:
        response = await dealt.client.get(VIEW, headers=dealt.credentials(SEATED))

    assert response.json()["seq"] > 0


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_token_speaks_for_the_seat_it_took_at_the_gathering(case: HostCase) -> None:
    async with playing(case.game) as dealt:
        served = [
            (await dealt.client.get(VIEW, headers=dealt.credentials(seat))).json()["observer"]
            for seat in range(PLAYERS)
        ]

    assert served == list(range(PLAYERS))


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_move_a_seat_is_offered_lands_through_the_host(case: HostCase) -> None:
    async with playing(case.game) as dealt:
        seat, move, base_seq = await a_seat_to_act(dealt)

        status = await submit(dealt, seat, move, base_seq)
        after = (await dealt.client.get(VIEW, headers=dealt.credentials(seat))).json()

    assert status == HTTPStatus.OK
    assert after["seq"] > base_seq


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
async def test_a_token_makes_no_move_for_another_seat(case: HostCase) -> None:
    async with playing(case.game) as dealt:
        seat, move, base_seq = await a_seat_to_act(dealt)
        impostor = (seat + 1) % PLAYERS

        status = await submit(dealt, impostor, move, base_seq)

    assert status == HTTPStatus.FORBIDDEN


def test_a_match_of_passing_is_dealt_for_the_seats_asked_for() -> None:
    assert a_passing_match(CHOICE, SEED).players == PLAYERS


def test_a_match_of_passing_is_dealt_from_as_many_decks_as_the_company_settled_on() -> None:
    """A deal from a count the rules refuse never returns, so a match in hand is one the decks were right for."""
    chosen = settled(GameName.PASSING, PLAYERS, TWO_DECKS)

    assert a_passing_match(chosen, SEED).players == PLAYERS


def test_a_match_of_showdown_runs_the_rounds_asked_for() -> None:
    assert a_showdown_match(CHOICE, SEED).position.state.rounds == ROUNDS


def test_a_match_of_shedding_runs_the_rounds_asked_for() -> None:
    assert a_shedding_match(CHOICE, SEED).position.state.rounds == ROUNDS


def test_a_match_of_climbing_runs_the_rounds_asked_for() -> None:
    assert a_climbing_match(CHOICE, SEED).position.state.rounds == ROUNDS


def test_every_game_a_host_deals_runs_to_the_ending_the_company_settled() -> None:
    """One conclusion opens any of them, which is what a match length settled at the table rather than in the
    rules buys."""
    chosen = CHOICE.model_copy(update={"conclusion": Conclusion(lead=A_LEAD)})
    matches = (
        a_passing_match(chosen, SEED),
        a_showdown_match(chosen, SEED),
        a_shedding_match(chosen, SEED),
        a_climbing_match(chosen, SEED),
    )

    for match in matches:
        assert match.position.state.lead == A_LEAD
        assert match.position.state.rounds is None


def test_a_table_gathers_under_the_name_the_settings_give_it() -> None:
    assert opened(SETTINGS, CHOICE, GLYPHS, ADVANCED).table == SETTINGS.name


def test_a_table_gathers_behind_the_code_the_settings_state() -> None:
    assert opened(SETTINGS, CHOICE, GLYPHS, ADVANCED).code == SETTINGS.code


def test_a_seating_no_game_is_played_at_gathers_no_table() -> None:
    """The rules of a game state the tables it seats, so a choice past them is refused as the room opens."""
    with pytest.raises(GameValidationError):
        opened(SETTINGS, settled(GameName.PASSING, SEATS_NO_GAME_HOLDS, ONE_DECK), GLYPHS, ADVANCED)


def test_a_count_of_decks_a_game_is_dealt_from_nowhere_gathers_no_table() -> None:
    with pytest.raises(GameValidationError):
        opened(SETTINGS, settled(GameName.SHOWDOWN, PLAYERS, TWO_DECKS), GLYPHS, ADVANCED)


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
def test_a_settled_choice_is_dealt_as_the_game_it_names(case: HostCase) -> None:
    """A gathering names a game and this is where the rules of that name are found, dealt and put in service."""
    tables = TableRegistry(NO_GRACE)

    Deals(tables, SEED).open(SETTINGS.name, settled(case.game, PLAYERS, ONE_DECK), a_seated_company(PLAYERS))

    assert tables.session(SETTINGS.name).layout(FIRST_SEAT).title == case.scene.title
