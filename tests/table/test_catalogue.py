from http import HTTPStatus
from random import Random

import pytest

from cardserver.naming import Named
from cardserver.registry import TableRegistry
from cardserver.remembering import FORGETFUL
from cardtable.catalogue import (
    TWO_DECKS,
    UNCOMMITTED,
    Deals,
    a_climbing_match,
    a_generator,
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

from .config import ADMIN, ADVANCED, GLYPHS, NOTHING_KEPT
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
    TABLE,
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
A_FEW_COMMITS = 7
ANOTHER_TABLE = "red-baize"


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
    assert a_passing_match(CHOICE, Random(SEED)).players == PLAYERS


def test_a_match_of_passing_is_dealt_from_as_many_decks_as_the_company_settled_on() -> None:
    """A deal from a count the rules refuse never returns, so a match in hand is one the decks were right for."""
    chosen = settled(GameName.PASSING, PLAYERS, TWO_DECKS)

    assert a_passing_match(chosen, Random(SEED)).players == PLAYERS


def test_a_match_of_showdown_runs_the_rounds_asked_for() -> None:
    assert a_showdown_match(CHOICE, Random(SEED)).position.state.rounds == ROUNDS


def test_a_match_of_shedding_runs_the_rounds_asked_for() -> None:
    assert a_shedding_match(CHOICE, Random(SEED)).position.state.rounds == ROUNDS


def test_a_match_of_climbing_runs_the_rounds_asked_for() -> None:
    assert a_climbing_match(CHOICE, Random(SEED)).position.state.rounds == ROUNDS


def test_every_game_a_host_deals_runs_to_the_ending_the_company_settled() -> None:
    """One conclusion opens any of them, which is what a match length settled at the table rather than in the
    rules buys."""
    chosen = CHOICE.model_copy(update={"conclusion": Conclusion(lead=A_LEAD)})
    matches = (
        a_passing_match(chosen, Random(SEED)),
        a_showdown_match(chosen, Random(SEED)),
        a_shedding_match(chosen, Random(SEED)),
        a_climbing_match(chosen, Random(SEED)),
    )

    for match in matches:
        assert match.position.state.lead == A_LEAD
        assert match.position.state.rounds is None


def test_a_table_gathers_under_the_name_the_settings_give_it() -> None:
    assert opened(SETTINGS, CHOICE, GLYPHS, ADVANCED, ADMIN, records=NOTHING_KEPT).table == SETTINGS.name


def test_a_table_gathers_behind_the_code_the_settings_state() -> None:
    assert opened(SETTINGS, CHOICE, GLYPHS, ADVANCED, ADMIN, records=NOTHING_KEPT).code == SETTINGS.code


def test_a_seating_no_game_is_played_at_gathers_no_table() -> None:
    """The rules of a game state the tables it seats, so a choice past them is refused as the room opens."""
    with pytest.raises(GameValidationError):
        opened(
            SETTINGS,
            settled(GameName.PASSING, SEATS_NO_GAME_HOLDS, ONE_DECK),
            GLYPHS,
            ADVANCED,
            ADMIN,
            records=NOTHING_KEPT,
        )


def test_a_count_of_decks_a_game_is_dealt_from_nowhere_gathers_no_table() -> None:
    with pytest.raises(GameValidationError):
        opened(SETTINGS, settled(GameName.SHOWDOWN, PLAYERS, TWO_DECKS), GLYPHS, ADVANCED, ADMIN, records=NOTHING_KEPT)


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
def test_a_settled_choice_is_dealt_as_the_game_it_names(case: HostCase) -> None:
    """A gathering names a game and this is where the rules of that name are found, dealt and put in service."""
    tables = TableRegistry(NO_GRACE, keeping=FORGETFUL)

    Deals(tables, SEED).open(SETTINGS.name, settled(case.game, PLAYERS, ONE_DECK), a_seated_company(PLAYERS))

    assert tables.session(SETTINGS.name).layout(FIRST_SEAT).title == case.scene.title


def test_a_run_stating_the_seed_it_announced_deals_the_match_it_dealt() -> None:
    """The seed is announced for exactly this, so it reads the same way however many times a run is started."""
    assert a_generator(SEED, TABLE, UNCOMMITTED).random() == a_generator(SEED, TABLE, UNCOMMITTED).random()


def test_two_tables_of_one_run_draw_from_streams_of_their_own() -> None:
    """A run holds one seed, so a guest who played a hand at one table would otherwise know the next one's."""
    assert a_generator(SEED, TABLE, UNCOMMITTED).random() != a_generator(SEED, ANOTHER_TABLE, UNCOMMITTED).random()


def test_a_table_taken_up_draws_where_the_run_that_dealt_it_never_drew() -> None:
    """A table resumed at its record's length draws onward rather than dealing the round already played."""
    assert a_generator(SEED, TABLE, UNCOMMITTED).random() != a_generator(SEED, TABLE, A_FEW_COMMITS).random()


def test_two_tables_dealt_by_one_run_hold_cards_of_their_own() -> None:
    """What the streams buy at the felt, where a lobby lets a guest gather a table beside the one they played."""
    tables = TableRegistry(NO_GRACE, keeping=FORGETFUL)
    deals = Deals(tables, SEED)

    deals.open(TABLE, CHOICE, a_seated_company(PLAYERS))
    deals.open(ANOTHER_TABLE, CHOICE, a_seated_company(PLAYERS))

    assert tables.session(TABLE).view(FIRST_SEAT) != tables.session(ANOTHER_TABLE).view(FIRST_SEAT)
