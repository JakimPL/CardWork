from typing import Final

from cardserver.naming import Seated
from cardserver.remembering import (
    FORGETFUL,
    RECORD_VERSION,
    Remembering,
    RoomRecord,
    Written,
    digest_of,
)
from cardserver.sessions import InService
from cardwork.states.state import GameState
from cardwork.zones.zones import hand_of

from ..games.demo import SEATS
from .company import CODE, COMPANY, Gathered, a_dealt_table, a_sealed_round, a_sealing, a_seated_company
from .conftest import BACKWARDS, TABLE
from .keeping import JOURNAL, ROOM, Keeping, a_journal, read_back

A_REASON: Final[str] = "closing up"
NOTHING_YET: Final[str] = "{}"


def keys_of(keeping: Keeping, table: str) -> tuple[str | None, ...]:
    """The key each commit of a table was landed under, in commit order."""
    return tuple(written.key for written in read_back(keeping.written(table)))


def test_a_room_is_written_down_as_it_is_gathered(gathered: Gathered) -> None:
    record = gathered.keeping.rooms[TABLE]

    assert record.table == TABLE
    assert record.code == CODE
    assert record.choice == a_sealed_round(SEATS)
    assert record.host is None
    assert record.democratic


def test_a_room_is_written_down_at_the_revision_it_hands_out(gathered: Gathered) -> None:
    """What a client is told is what a run reading the room back stands at, so a command built on it lands."""
    gathering = gathered.gathering

    for name in COMPANY:
        gathering.admit(name)

        assert gathered.keeping.rooms[TABLE].revision == gathering.view(name).revision


def test_every_change_a_room_goes_through_is_written_down(gathered: Gathered) -> None:
    written = gathered.keeping.writes
    gathered.gathering.admit("Ada")
    gathered.gathering.claim("Ada", 0, gathered.gathering.revision)

    assert gathered.keeping.writes == written + 2


def test_the_record_holds_a_digest_of_every_token_and_never_a_token(gathered: Gathered) -> None:
    """The one thing on disk that would admit somebody, kept as a mark that answers the room and nobody else."""
    token = gathered.gathering.admit("Ada")

    record = gathered.keeping.rooms[TABLE]

    assert record.tokens == {digest_of(token): "Ada"}
    assert token not in record.model_dump_json()


def test_the_record_holds_the_company_and_where_they_settled_to_sit(gathered: Gathered) -> None:
    a_seated_company(gathered)

    record = gathered.keeping.rooms[TABLE]

    assert record.seats == {name: seat for seat, name in enumerate(COMPANY)}
    assert record.ready == dict.fromkeys(COMPANY, True)
    assert record.tints.keys() == set(COMPANY)


def test_the_record_holds_the_seating_the_plaques_of_a_dealt_table_carry(gathered: Gathered) -> None:
    a_dealt_table(gathered)

    record = gathered.keeping.rooms[TABLE]

    assert record.dealt
    assert record.seated == {seat: Seated(name=name, tint=record.tints[name]) for seat, name in enumerate(COMPANY)}


def test_a_room_broken_up_is_written_down_broken_up(gathered: Gathered) -> None:
    gathered.gathering.close(A_REASON)

    record = gathered.keeping.rooms[TABLE]

    assert record.closed
    assert record.reason == A_REASON


def test_a_room_cleared_away_is_forgotten(gathered: Gathered) -> None:
    gathered.gatherings.drop(TABLE)

    assert TABLE not in gathered.keeping.rooms
    assert gathered.keeping.forgotten == [TABLE]


def test_a_room_record_travels_through_json_as_the_record_it_was(gathered: Gathered) -> None:
    a_seated_company(gathered)
    record = gathered.keeping.rooms[TABLE]

    read_back = RoomRecord.model_validate_json(record.model_dump_json())

    assert read_back == record
    assert read_back.version == RECORD_VERSION


def test_a_table_is_written_down_as_it_is_dealt(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    session = gathered.registry.session(TABLE)

    assert gathered.keeping.origins[TABLE]
    assert len(gathered.keeping.commits[TABLE]) == session.head


def test_the_record_a_deal_opens_reads_back_as_the_journal_the_table_holds(gathered: Gathered) -> None:
    """The whole point of writing a table down, read through the seam a host resuming one reads it through."""
    a_dealt_table(gathered)
    session = gathered.registry.session(TABLE)
    session.reveal()

    assert a_journal(gathered.keeping.written(TABLE)) == session.record


def test_the_table_is_written_down_before_the_room_that_names_it_dealt(gathered: Gathered) -> None:
    """A journal is the mark a deal leaves, so it lands first and a torn record still reads as a dealt table."""
    a_dealt_table(gathered)

    order = gathered.keeping.order

    assert order[-1] == ROOM
    assert JOURNAL in order[:-1]


async def test_a_move_is_written_down_under_the_key_it_landed_by(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    session: InService = gathered.registry.session(TABLE)

    await session.submit(a_sealing(0), session.head, "seal-0")

    written = Written[GameState].model_validate_json(gathered.keeping.commits[TABLE][-1])
    assert written.key == "seal-0"
    assert written.transaction.seq == session.head - 1


async def test_an_arrangement_is_written_down_under_the_key_it_landed_by(gathered: Gathered) -> None:
    a_dealt_table(gathered)
    session: InService = gathered.registry.session(TABLE)

    await session.arrange(hand_of(0), BACKWARDS, 0, session.head, "sort-0")

    written = Written[GameState].model_validate_json(gathered.keeping.commits[TABLE][-1])
    assert written.key == "sort-0"
    assert written.transaction.seq == session.head - 1


async def test_a_commit_the_rules_owed_is_written_down_under_no_key(gathered: Gathered) -> None:
    """A settlement is the table's own, so it reaches the record like any commit and names no client's try."""
    a_dealt_table(gathered)
    session: InService = gathered.registry.session(TABLE)
    for seat in range(SEATS):
        await session.submit(a_sealing(seat), session.head, f"seal-{seat}")

    await session.drain()

    assert len(gathered.keeping.commits[TABLE]) == session.head
    assert keys_of(gathered.keeping, TABLE)[-1] is None


async def test_a_table_broken_up_is_forgotten(gathered: Gathered) -> None:
    a_dealt_table(gathered)

    await gathered.registry.dismiss(TABLE, A_REASON)

    assert TABLE not in gathered.keeping.origins
    assert TABLE not in gathered.keeping.commits


def test_a_room_still_settling_is_read_back_holding_no_table(gathered: Gathered) -> None:
    (kept,) = gathered.keeping.kept()

    assert kept.room.dealt is False
    assert kept.table is None


def test_a_room_that_was_dealt_is_read_back_holding_the_table_it_became(gathered: Gathered) -> None:
    a_dealt_table(gathered)

    (kept,) = gathered.keeping.kept()

    assert kept.room.dealt
    assert kept.table is not None
    assert kept.table.commits


def test_a_host_keeping_nothing_takes_every_word_and_holds_none(gathered: Gathered) -> None:
    """What a run gathering tables for its own lifetime holds, which leaves every writer free of the question."""
    forgetful: Remembering = FORGETFUL

    forgetful.remember_room(gathered.keeping.rooms[TABLE])
    forgetful.open_journal(TABLE, NOTHING_YET)
    forgetful.append(TABLE, NOTHING_YET)
    forgetful.set_aside(TABLE)
    forgetful.forget(TABLE)

    assert forgetful.kept() == ()
