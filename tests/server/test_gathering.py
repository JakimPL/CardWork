import json
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, Final

import pytest
from httpx import AsyncClient, Response
from pydantic import ValidationError

from cardserver.gathering import TINTS
from cardserver.naming import Seated
from cardserver.schemas import Choice, Choosing, Dealing, Offering, Tinting
from cardwork.games.capacity import Capacity
from cardwork.presentation.tint import Tint
from cardwork.rounds.conclusion import Conclusion

from ..games.demo import SEATS
from .company import (
    CODE,
    GAME,
    ONE_DECK,
    OTHER_GAME,
    OTHER_TITLE,
    ROUNDS,
    TWO_DECKS,
    Gathered,
    a_sealed_round,
)
from .conftest import (
    ATTENDANCE,
    CHOICE,
    DEALING,
    GATHERING,
    LAYOUT,
    MOVES,
    OFFERED,
    TABLE,
    TABLES,
    TINT,
    arrives,
    arriving,
    holding,
    sealing,
    seated_company,
    sits,
)
from .harness import Streamed
from .layout import TITLE

DATA: Final[str] = "data: "
COMPANY: Final[tuple[str, ...]] = ("Ada", "Grace", "Alan")
STANDING: Final[None] = None
A_SMALLER_TABLE: Final[int] = 2
PAST_THE_TABLE: Final[int] = SEATS + 1

SEATED_COMPANY: Final[Mapping[int, Seated]] = {
    seat: Seated(name=name, tint=TINTS[seat]) for seat, name in enumerate(COMPANY)
}
A_FREE_TINT: Final[Tint] = TINTS[-1]


def payload(written: str) -> dict[str, Any]:
    """The gathering carried by one frame, read the way a client reads the data line of it."""
    lines = [line for line in written.splitlines() if line.startswith(DATA)]
    return dict(json.loads(lines[0].removeprefix(DATA)))


def guest_named(view: dict[str, Any], name: str) -> dict[str, Any]:
    """One guest as the company of a gathering reads them."""
    return next(guest for guest in view["company"] if guest["name"] == name)


async def read_by(client: AsyncClient, token: str) -> dict[str, Any]:
    """The gathering as the guest holding one token reads it."""
    return dict((await client.get(GATHERING, headers=holding(token))).json())


async def chooses(
    client: AsyncClient,
    token: str,
    choice: Choice,
    base_revision: int,
) -> Response:
    """One guest settling what the table plays."""
    return await client.put(
        CHOICE,
        json=Choosing(choice=choice, base_revision=base_revision).model_dump(mode="json"),
        headers=holding(token),
    )


async def deals(client: AsyncClient, token: str, base_revision: int) -> Response:
    """One guest calling for the deal."""
    return await client.post(
        DEALING,
        json=Dealing(base_revision=base_revision).model_dump(mode="json"),
        headers=holding(token),
    )


async def takes(client: AsyncClient, token: str, tint: Tint, base_revision: int) -> Response:
    """One guest taking a tint of the company's."""
    return await client.put(
        TINT,
        json=Tinting(tint=tint, base_revision=base_revision).model_dump(mode="json"),
        headers=holding(token),
    )


def test_a_name_already_gathering_is_left_as_it_was(gathered: Gathered) -> None:
    with pytest.raises(ValueError, match="already gathering"):
        gathered.gatherings.open(
            TABLE,
            CODE,
            a_sealed_round(SEATS),
            democratic=False,
        )


@pytest.mark.parametrize(
    "decks",
    [
        pytest.param((), id="a game naming no count at all"),
        pytest.param((0,), id="a game dealt from no deck"),
        pytest.param((ONE_DECK, 0), id="a game dealt from one deck or none"),
    ],
)
def test_a_game_names_the_whole_decks_it_is_dealt_from(decks: tuple[int, ...]) -> None:
    with pytest.raises(ValidationError, match="dealt from whole decks"):
        Offering(
            game=GAME,
            title=TITLE,
            seats=Capacity(least=A_SMALLER_TABLE, most=SEATS),
            decks=decks,
        )


async def test_a_host_says_which_games_it_offers(visitor: AsyncClient) -> None:
    offered = (await visitor.get(OFFERED)).json()

    assert [offering["game"] for offering in offered] == [GAME, OTHER_GAME]
    assert offered[1] == {
        "game": OTHER_GAME,
        "title": OTHER_TITLE,
        "seats": {"least": 2, "most": 4},
        "decks": [ONE_DECK, TWO_DECKS],
    }


async def test_a_guest_takes_a_seat_and_the_company_reads_them_at_it(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    token = await arrives(visitor, "Ada")
    answered = await sits(visitor, token, 1, gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.OK
    assert guest_named(answered.json(), "Ada")["seat"] == 1


async def test_a_guest_stands_up_from_the_seat_they_hold_by_naming_none(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    token = await arrives(visitor, "Ada")
    await sits(visitor, token, 1, gathered.gathering.revision)
    answered = await sits(visitor, token, STANDING, gathered.gathering.revision)

    assert guest_named(answered.json(), "Ada")["seat"] is None


async def test_a_seat_another_guest_holds_is_left_as_it_was(visitor: AsyncClient, gathered: Gathered) -> None:
    held = await arrives(visitor, "Ada")
    await sits(visitor, held, 1, gathered.gathering.revision)
    asking = await arrives(visitor, "Grace")
    answered = await sits(visitor, asking, 1, gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.CONFLICT
    assert guest_named(await read_by(visitor, held), "Ada")["seat"] == 1


async def test_a_guest_takes_the_seat_they_already_hold_and_keeps_it(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    token = await arrives(visitor, "Ada")
    await sits(visitor, token, 1, gathered.gathering.revision)
    answered = await sits(visitor, token, 1, gathered.gathering.revision)

    assert guest_named(answered.json(), "Ada")["seat"] == 1


async def test_a_seat_the_table_holds_nowhere_is_claimed_by_nobody(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    token = await arrives(visitor, "Ada")
    answered = await sits(visitor, token, PAST_THE_TABLE, gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_a_command_built_on_a_revision_the_gathering_moved_past_is_refused(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    token = await arrives(visitor, "Ada")
    stale = gathered.gathering.revision
    await arrives(visitor, "Grace")
    answered = await sits(visitor, token, 1, stale)

    assert answered.status_code == HTTPStatus.CONFLICT


async def test_a_guest_takes_a_tint_no_one_else_holds(visitor: AsyncClient, gathered: Gathered) -> None:
    token = await arrives(visitor, "Ada")
    answered = await takes(visitor, token, A_FREE_TINT, gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.OK
    assert guest_named(answered.json(), "Ada")["tint"] == A_FREE_TINT.value


async def test_a_tint_another_guest_holds_is_left_as_it_was(visitor: AsyncClient, gathered: Gathered) -> None:
    held = await arrives(visitor, "Ada")
    asking = await arrives(visitor, "Grace")
    answered = await takes(visitor, asking, TINTS[0], gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.CONFLICT
    assert guest_named(await read_by(visitor, held), "Ada")["tint"] == TINTS[0].value


async def test_a_guest_takes_the_tint_they_already_hold_and_keeps_it(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    token = await arrives(visitor, "Ada")
    answered = await takes(visitor, token, TINTS[0], gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.OK
    assert guest_named(answered.json(), "Ada")["tint"] == TINTS[0].value


async def test_a_tint_is_a_guest_s_own_whether_they_are_sitting_or_standing(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    """A tint belongs to a guest rather than to a seat, so standing up leaves it where it was."""
    token = await arrives(visitor, "Ada")
    await takes(visitor, token, A_FREE_TINT, gathered.gathering.revision)
    await sits(visitor, token, 1, gathered.gathering.revision)
    answered = await sits(visitor, token, STANDING, gathered.gathering.revision)

    assert guest_named(answered.json(), "Ada")["tint"] == A_FREE_TINT.value


async def test_a_tint_taken_on_a_revision_the_gathering_moved_past_is_refused(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    token = await arrives(visitor, "Ada")
    stale = gathered.gathering.revision
    await arrives(visitor, "Grace")
    answered = await takes(visitor, token, A_FREE_TINT, stale)

    assert answered.status_code == HTTPStatus.CONFLICT


async def test_a_guest_standing_at_no_seat_settles_nothing(visitor: AsyncClient, gathered: Gathered) -> None:
    token = await arrives(visitor, "Ada")
    answered = await chooses(visitor, token, a_sealed_round(A_SMALLER_TABLE), gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.FORBIDDEN


async def test_a_seated_guest_settles_what_the_table_plays(visitor: AsyncClient, gathered: Gathered) -> None:
    token = await arrives(visitor, "Ada")
    await sits(visitor, token, 0, gathered.gathering.revision)
    answered = await chooses(visitor, token, a_sealed_round(A_SMALLER_TABLE), gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.OK
    assert answered.json()["choice"]["players"] == A_SMALLER_TABLE


async def test_a_smaller_table_stands_up_whoever_sat_past_the_seats_it_holds(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    settling = await arrives(visitor, "Ada")
    await sits(visitor, settling, 0, gathered.gathering.revision)
    outside = await arrives(visitor, "Grace")
    await sits(visitor, outside, A_SMALLER_TABLE, gathered.gathering.revision)
    answered = await chooses(visitor, settling, a_sealed_round(A_SMALLER_TABLE), gathered.gathering.revision)

    assert guest_named(answered.json(), "Grace")["seat"] is None
    assert guest_named(answered.json(), "Ada")["seat"] == 0


async def test_a_game_this_host_offers_nowhere_is_played_nowhere(visitor: AsyncClient, gathered: Gathered) -> None:
    token = await arrives(visitor, "Ada")
    await sits(visitor, token, 0, gathered.gathering.revision)
    asking = Choice(game="whist", players=SEATS, decks=ONE_DECK, conclusion=Conclusion(rounds=ROUNDS))
    answered = await chooses(visitor, token, asking, gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "whist" in answered.json()["detail"]


async def test_a_table_the_game_seats_nowhere_is_settled_on_by_nobody(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    token = await arrives(visitor, "Ada")
    await sits(visitor, token, 0, gathered.gathering.revision)
    answered = await chooses(visitor, token, a_sealed_round(1), gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "2 to 4 players" in answered.json()["detail"]


async def test_a_count_of_decks_the_game_is_dealt_from_nowhere_is_refused(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    token = await arrives(visitor, "Ada")
    await sits(visitor, token, 0, gathered.gathering.revision)
    asking = Choice(game=GAME, players=SEATS, decks=TWO_DECKS, conclusion=Conclusion(rounds=ROUNDS))
    answered = await chooses(visitor, token, asking, gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "1 decks" in answered.json()["detail"]


async def test_a_table_with_a_seat_standing_empty_is_dealt_by_nobody(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    token = await arrives(visitor, "Ada")
    await sits(visitor, token, 0, gathered.gathering.revision)
    answered = await deals(visitor, token, gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.CONFLICT
    assert "[1, 2]" in answered.json()["detail"]
    assert gathered.deals.dealt == []


async def test_a_full_table_is_dealt_and_the_gathering_is_over(visitor: AsyncClient, gathered: Gathered) -> None:
    tokens = await seated_company(visitor, COMPANY)
    answered = await deals(visitor, tokens[0], gathered.gathering.revision)

    assert answered.status_code == HTTPStatus.OK
    assert answered.json()["dealt"] is True
    assert gathered.gathering.dealt is True


async def test_the_deal_opens_the_table_the_company_settled_on(visitor: AsyncClient, gathered: Gathered) -> None:
    tokens = await seated_company(visitor, COMPANY)
    await deals(visitor, tokens[0], gathered.gathering.revision)

    dealt = gathered.deals.dealt

    assert [table for table, _, _ in dealt] == [TABLE]
    assert dealt[0][1] == a_sealed_round(SEATS)
    assert dealt[0][2] == SEATED_COMPANY


async def test_the_table_reads_every_plaque_by_the_name_its_guest_arrived_under(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    tokens = await seated_company(visitor, COMPANY)
    await deals(visitor, tokens[0], gathered.gathering.revision)

    layout = (await visitor.get(LAYOUT, headers=holding(tokens[0]))).json()

    assert [plaque["name"] for plaque in layout["plaques"]] == list(COMPANY)


async def test_the_table_reads_every_plaque_under_the_tint_its_guest_holds(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    tokens = await seated_company(visitor, COMPANY)
    await deals(visitor, tokens[0], gathered.gathering.revision)

    layout = (await visitor.get(LAYOUT, headers=holding(tokens[0]))).json()

    assert [plaque["tint"] for plaque in layout["plaques"]] == [tint.value for tint in TINTS[: len(COMPANY)]]


async def test_the_token_that_took_a_seat_is_the_one_that_plays_it(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    tokens = await seated_company(visitor, COMPANY)
    await deals(visitor, tokens[0], gathered.gathering.revision)

    session = gathered.registry.session(TABLE)
    answered = await visitor.post(MOVES, json=sealing(1, session.head, "first"), headers=holding(tokens[1]))

    assert answered.status_code == HTTPStatus.OK
    assert (await visitor.get(GATHERING, headers=holding(tokens[1]))).json()["mine"] == "Grace"


async def test_a_seat_is_played_by_nobody_holding_another_seat_s_token(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    tokens = await seated_company(visitor, COMPANY)
    await deals(visitor, tokens[0], gathered.gathering.revision)

    session = gathered.registry.session(TABLE)
    answered = await visitor.post(MOVES, json=sealing(1, session.head, "first"), headers=holding(tokens[0]))

    assert answered.status_code == HTTPStatus.FORBIDDEN


async def test_a_client_offering_no_token_watches_a_dealt_table(visitor: AsyncClient, gathered: Gathered) -> None:
    tokens = await seated_company(visitor, COMPANY)
    await deals(visitor, tokens[0], gathered.gathering.revision)

    answered = await visitor.get(LAYOUT)

    assert answered.status_code == HTTPStatus.OK
    assert answered.json()["observer"] is None


async def test_a_guest_holding_a_token_the_gathering_never_minted_plays_nothing(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    tokens = await seated_company(visitor, COMPANY)
    await deals(visitor, tokens[0], gathered.gathering.revision)

    answered = await visitor.get(LAYOUT, headers=holding("picked-up-somewhere"))

    assert answered.status_code == HTTPStatus.UNAUTHORIZED


async def test_a_gathering_over_is_asked_for_nothing_more(visitor: AsyncClient, gathered: Gathered) -> None:
    tokens = await seated_company(visitor, COMPANY)
    await deals(visitor, tokens[0], gathered.gathering.revision)
    standing = gathered.gathering.revision

    asked = (
        await sits(visitor, tokens[0], 2, standing),
        await takes(visitor, tokens[0], A_FREE_TINT, standing),
        await chooses(visitor, tokens[0], a_sealed_round(A_SMALLER_TABLE), standing),
        await deals(visitor, tokens[0], standing),
        await arriving(visitor, "Late"),
    )

    assert [answered.status_code for answered in asked] == [HTTPStatus.CONFLICT] * len(asked)


async def test_a_table_gathering_is_named_to_whoever_reached_the_server_bare(visitor: AsyncClient) -> None:
    assert (await visitor.get(TABLES)).json() == [TABLE]


async def test_a_table_dealt_is_named_to_nobody_arriving_since_its_gathering_is_over(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    tokens = await seated_company(visitor, COMPANY)
    await deals(visitor, tokens[0], gathered.gathering.revision)

    assert (await visitor.get(TABLES)).json() == []


async def test_a_gathering_over_still_reads_for_the_company_that_settled_it(
    visitor: AsyncClient,
    gathered: Gathered,
) -> None:
    tokens = await seated_company(visitor, COMPANY)
    await deals(visitor, tokens[0], gathered.gathering.revision)

    read = await read_by(visitor, tokens[2])

    assert read["dealt"] is True
    assert guest_named(read, "Alan")["seat"] == 2


async def test_a_stream_opens_on_the_gathering_as_it_stands(visitor: AsyncClient, gathered: Gathered) -> None:
    token = await arrives(visitor, "Ada")

    async with Streamed(gathered.app, ATTENDANCE, holding(token)) as stream:
        status = await stream.status()
        written = await stream.frame()

    assert status == HTTPStatus.OK
    assert written.startswith("id: ")
    assert payload(written)["mine"] == "Ada"


async def test_a_guest_holding_a_stream_is_read_as_present(visitor: AsyncClient, gathered: Gathered) -> None:
    watching = await arrives(visitor, "Ada")
    reading = await arrives(visitor, "Grace")

    async with Streamed(gathered.app, ATTENDANCE, holding(watching)) as stream:
        await stream.status()
        await stream.frame()
        read = await read_by(visitor, reading)

    assert guest_named(read, "Ada")["present"] is True
    assert guest_named(read, "Grace")["present"] is False


async def test_a_guest_who_hung_up_is_read_as_gone(visitor: AsyncClient, gathered: Gathered) -> None:
    watching = await arrives(visitor, "Ada")
    reading = await arrives(visitor, "Grace")

    async with Streamed(gathered.app, ATTENDANCE, holding(watching)) as stream:
        await stream.status()
        await stream.frame()

    assert guest_named(await read_by(visitor, reading), "Ada")["present"] is False


async def test_a_stream_carries_the_gathering_again_as_it_changes(visitor: AsyncClient, gathered: Gathered) -> None:
    watching = await arrives(visitor, "Ada")

    async with Streamed(gathered.app, ATTENDANCE, holding(watching)) as stream:
        await stream.status()
        await stream.frame()
        await arrives(visitor, "Grace")
        written = await stream.frame()

    assert guest_named(payload(written), "Grace")["seat"] is None


async def test_a_stream_resumes_after_the_revision_a_client_read(visitor: AsyncClient, gathered: Gathered) -> None:
    token = await arrives(visitor, "Ada")
    read = gathered.gathering.revision
    await arrives(visitor, "Grace")

    async with Streamed(gathered.app, ATTENDANCE, {**holding(token), "Last-Event-ID": str(read)}) as stream:
        await stream.status()
        written = await stream.frame()

    assert payload(written)["revision"] > read


async def test_the_deal_is_the_last_thing_a_stream_carries(visitor: AsyncClient, gathered: Gathered) -> None:
    tokens = await seated_company(visitor, COMPANY)

    async with Streamed(gathered.app, ATTENDANCE, holding(tokens[0])) as stream:
        await stream.status()
        await stream.frame()
        await deals(visitor, tokens[0], gathered.gathering.revision)
        written = await stream.frame()
        closed = await stream.frame()

    assert payload(written)["dealt"] is True
    assert closed == ""
