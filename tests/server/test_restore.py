import asyncio
from typing import Final

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from cardserver.errors import GatheringOver, StaleGathering, TableTaken, Unauthenticated
from cardserver.gathering import Gathering
from cardserver.sessions import InService
from cardwork.zones.zones import hand_of

from ..games.demo import SEATS
from .company import (
    COMPANY,
    Gathered,
    Rig,
    a_dealt_table,
    a_rig,
    a_sealing,
    a_seated_company,
    restarted,
)
from .conftest import BACKWARDS, DEAL, EVENTS, MOVES, TABLE, credentials, sealing
from .harness import PATIENCE, Following, an_event_id
from .keeping import a_journal, applied_of

A_REASON: Final[str] = "closing up"
A_STRANGER: Final[str] = "token-from-nowhere"
A_KEY: Final[str] = "seal-0"
A_SORT: Final[str] = "sort-0"
ANOTHER_NAME: Final[str] = "Barbara"
ANOTHER_TABLE: Final[str] = "no-such-table"
FROM_THE_FUTURE: Final[int] = 500
SCORED: Final[str] = "score"
RESUME_HEADER: Final[str] = "Last-Event-ID"
ONE_CHANGE: Final[int] = 1


def room_of(rig: Rig) -> Gathering:
    """The room a restarted run holds under the name these tests gather at."""
    return rig.gatherings.at(TABLE)


def table_of(rig: Rig) -> InService:
    """The table a restarted run serves under the name these tests gather at."""
    return rig.registry.session(TABLE)


def test_a_restored_room_reads_to_a_guest_as_the_room_they_left(gathered: Gathered) -> None:
    """The whole of what a page draws, handed back to the guest who was reading it before the run ended."""
    a_seated_company(gathered)
    before = gathered.gathering.view(COMPANY[0])

    after = room_of(restarted(gathered)).view(COMPANY[0])

    assert after.table == before.table
    assert after.code == before.code
    assert after.choice == before.choice
    assert after.democratic == before.democratic
    assert tuple(guest.name for guest in after.company) == tuple(guest.name for guest in before.company)
    assert tuple(guest.seat for guest in after.company) == tuple(guest.seat for guest in before.company)
    assert tuple(guest.tint for guest in after.company) == tuple(guest.tint for guest in before.company)
    assert tuple(guest.ready for guest in after.company) == tuple(guest.ready for guest in before.company)


def test_a_token_minted_before_the_restart_still_holds_its_seat(gathered: Gathered) -> None:
    """What makes a restart invisible: the address in a page's own bar names the seat it held all along."""
    tokens = a_seated_company(gathered)

    rig = restarted(gathered)

    for seat, name in enumerate(COMPANY):
        assert rig.gatherings.seat(TABLE, tokens[name]) == seat
        assert rig.gatherings.guest(TABLE, tokens[name]) == name


def test_a_token_minted_at_no_room_a_run_read_back_speaks_for_nobody(gathered: Gathered) -> None:
    a_seated_company(gathered)

    rig = restarted(gathered)

    with pytest.raises(Unauthenticated):
        rig.gatherings.guest(TABLE, A_STRANGER)


def test_a_restored_room_is_read_as_a_room_nobody_is_at(gathered: Gathered) -> None:
    """Presence is a fact about a stream rather than about a room, and no stream outlives the run holding it."""
    a_seated_company(gathered)
    gathered.gathering.attends(COMPANY[0])

    room = room_of(restarted(gathered))

    assert room.present == 0
    assert all(not guest.present for guest in room.view(COMPANY[0]).company)


def test_a_restored_room_stands_one_change_past_the_revision_it_was_written_at(gathered: Gathered) -> None:
    a_seated_company(gathered)
    written = gathered.keeping.rooms[TABLE].revision

    assert room_of(restarted(gathered)).revision == written + ONE_CHANGE


def test_a_command_built_before_the_restart_is_refused_rather_than_landing(gathered: Gathered) -> None:
    """The room moved under it while it was away, so the page is sent to read the company as it now stands."""
    a_seated_company(gathered)
    held = gathered.gathering.revision

    room = room_of(restarted(gathered))

    with pytest.raises(StaleGathering):
        room.claim(COMPANY[0], None, held)


def test_a_restored_room_is_written_down_afresh_only_once_it_changes(gathered: Gathered) -> None:
    """A room read back is a room a run found rather than one it gathered, so nothing is laid over the record."""
    a_seated_company(gathered)
    written = gathered.keeping.writes

    room = room_of(restarted(gathered))

    assert gathered.keeping.writes == written

    room.claim(COMPANY[0], None, room.revision)

    assert gathered.keeping.writes == written + ONE_CHANGE


def test_a_room_broken_up_before_the_restart_is_read_back_broken_up(gathered: Gathered) -> None:
    a_seated_company(gathered)
    gathered.gathering.close(A_REASON)

    room = room_of(restarted(gathered))

    assert room.closed
    assert room.reason == A_REASON


def test_a_room_dealt_before_the_restart_admits_nobody_further(gathered: Gathered) -> None:
    a_dealt_table(gathered)

    room = room_of(restarted(gathered))

    assert room.dealt
    with pytest.raises(GatheringOver):
        room.admit(ANOTHER_NAME)


def test_a_room_written_down_before_its_deal_was_is_taken_back_as_the_dealt_room_it_became(
    gathered: Gathered,
) -> None:
    """A journal is the mark a deal leaves, so a run holding one reads the room dealt whatever the room says."""
    a_seated_company(gathered)
    still_gathering = gathered.keeping.rooms[TABLE]

    room = a_rig(gathered.keeping).gatherings.restore(still_gathering, dealt=True)

    assert not still_gathering.dealt
    assert room.dealt


def test_a_run_says_whether_it_already_stands_at_a_name(gathered: Gathered) -> None:
    """What a run asks before gathering the table it announces, since the room may have been read back."""
    rig = restarted(gathered)

    assert rig.gatherings.stands(TABLE)
    assert not rig.gatherings.stands(ANOTHER_TABLE)


def test_a_record_of_a_room_already_gathering_is_refused(gathered: Gathered) -> None:
    record = gathered.keeping.rooms[TABLE]

    rig = restarted(gathered)

    with pytest.raises(TableTaken):
        rig.gatherings.restore(record, dealt=record.dealt)


def test_a_restored_table_stands_where_its_last_commit_left_it(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    session: InService = gathered.registry.session(TABLE)

    table = table_of(restarted(gathered))

    assert table.head == session.head
    assert table.view(0) == session.view(0)


async def test_a_table_read_back_takes_the_move_a_table_that_never_stopped_would(gathered: Gathered) -> None:
    a_dealt_table(gathered)

    table = table_of(restarted(gathered))
    await table.submit(a_sealing(0), table.head, A_KEY)

    assert table.view(0).state.to_act == frozenset(range(SEATS)) - {0}


async def test_a_restored_table_answers_an_attempt_it_had_applied_with_the_sequence_it_reached(
    gathered: Gathered,
) -> None:
    """The keys travel in the record beside the commits they landed, so a retry lands once across a restart."""
    a_dealt_table(gathered)
    session: InService = gathered.registry.session(TABLE)
    landed = await session.submit(a_sealing(0), session.head, A_KEY)

    table = table_of(restarted(gathered))

    assert await table.submit(a_sealing(0), table.head, A_KEY) == landed
    assert table.head == session.head


async def test_an_arrangement_made_before_the_restart_comes_back_with_the_table(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    session: InService = gathered.registry.session(TABLE)
    await session.arrange(hand_of(0), BACKWARDS, 0, session.head, A_SORT)

    table = table_of(restarted(gathered))

    assert table.view(0) == session.view(0)


async def test_a_commit_landing_after_a_restart_is_laid_into_the_record_that_was_already_there(
    gathered: Gathered,
) -> None:
    """The record a table opens at is the record it holds, so what a store next hears is the next line of it."""
    a_dealt_table(gathered)
    written = len(gathered.keeping.commits[TABLE])

    table = table_of(restarted(gathered))
    await table.submit(a_sealing(0), table.head, A_KEY)

    record = gathered.keeping.written(TABLE)
    assert len(record.commits) == written + ONE_CHANGE
    assert a_journal(record).head == table.head
    assert applied_of(record)[A_KEY] == table.head - ONE_CHANGE


async def test_a_table_cut_off_inside_its_window_settles_what_it_owed_as_it_is_taken_up(
    gathered: Gathered,
) -> None:
    """A window belongs to the process that opened it, so nothing was ever going to wake this one.

    Every seat has acted and the rules owe the round its reveal and its score, held back for the moment a
    seat has to take a commitment back. The run ends there, before that moment has passed, dropping the
    window with everything else it was holding. The run started after it opens the table owing exactly that,
    settles it, and lays what it settled into the record before a client has read a word of the table.
    """
    a_dealt_table(gathered)
    session: InService = gathered.registry.session(TABLE)
    for seat in range(SEATS):
        await session.submit(a_sealing(seat), session.head, f"{A_KEY}-{seat}")

    await gathered.registry.close()
    held = session.head

    table = table_of(restarted(gathered))

    assert table.view(0).state.phase == SCORED
    assert table.head > held
    assert a_journal(gathered.keeping.written(TABLE)).head == table.head


def test_a_restored_table_carries_the_plaques_the_company_settled(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    session: InService = gathered.registry.session(TABLE)

    table = table_of(restarted(gathered))

    assert table.layout(0) == session.layout(0)


def test_a_record_of_a_table_already_in_service_is_refused(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    rig = restarted(gathered)
    (kept,) = gathered.keeping.kept()

    assert kept.table is not None
    with pytest.raises(TableTaken):
        rig.deals.resume(kept.room, kept.table)


async def test_a_page_holding_a_revision_from_before_the_restart_is_answered_rather_than_left_waiting(
    gathered: Gathered,
) -> None:
    """One poll, one frame, and the page reads the company as it stands rather than hanging on a lost past."""
    a_seated_company(gathered)
    held = gathered.gathering.revision

    room = room_of(restarted(gathered))

    view = await asyncio.wait_for(room.since(held + ONE_CHANGE, COMPANY[0]), PATIENCE)
    assert view.revision == room.revision


async def test_a_page_asking_after_a_revision_a_room_has_never_stood_at_is_answered_at_once(
    gathered: Gathered,
) -> None:
    """A cursor from a room this one has never been, which a page holds after a name was gathered afresh."""
    a_seated_company(gathered)

    view = await asyncio.wait_for(gathered.gathering.since(FROM_THE_FUTURE, COMPANY[0]), PATIENCE)

    assert view.revision == gathered.gathering.revision


async def test_a_stream_asking_from_beyond_the_record_is_carried_back_by_the_next_commit(
    app: FastAPI,
    client: AsyncClient,
) -> None:
    """A page holding the sequence of a table that once stood under this name reads where the record really goes."""
    headers = {**credentials(0), RESUME_HEADER: str(FROM_THE_FUTURE)}

    async with Following(app, EVENTS, headers) as stream:
        await client.post(MOVES, json=sealing(0, DEAL, A_KEY), headers=credentials(0))
        carried = await stream.frame()

    assert an_event_id(carried) == DEAL
