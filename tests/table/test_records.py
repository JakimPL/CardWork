from dataclasses import dataclass
from json import dumps, loads
from pathlib import Path
from stat import S_IMODE
from typing import Final

import pytest

from cardserver.naming import Seated
from cardserver.remembering import FORGETFUL, RECORD_VERSION, Kept, RoomRecord
from cardserver.schemas import Choice
from cardtable.games import GameName
from cardtable.paths import RECORDS, REPOSITORY
from cardtable.records import Ledger, Records, RecordUnread, StoreTaken, a_directory_name, a_ledger
from cardtable.records.naming import JOURNAL_FILE, ORIGIN_FILE, ROOM_FILE, SET_ASIDE
from cardtable.records.reading import whole_lines
from cardtable.records.writing import DIRECTORY_MODE, FILE_MODE
from cardwork.presentation.tint import Tint
from cardwork.rounds.conclusion import Conclusion
from tests.cases import Case, descriptions

TABLE: Final[str] = "green-baize"
ANOTHER_TABLE: Final[str] = "red-baize"
CODE: Final[str] = "KQAJ72"
PLAYERS: Final[int] = 3
ROUNDS: Final[int] = 2
ONE_DECK: Final[int] = 1
FIRST_REVISION: Final[int] = 0
NO_PATIENCE: Final[float] = 0.0
AN_ORIGIN: Final[str] = '{"seq": 0}'
A_COMMIT: Final[str] = '{"key": "seal-0"}'
ANOTHER_COMMIT: Final[str] = '{"key": "seal-1"}'
A_TORN_COMMIT: Final[str] = '{"key": "seal-2"'
NOT_A_ROOM: Final[str] = "this is no record of anything"
KEPT: Final[Records] = Records(kept=True, directory=None)
NOTHING_KEPT: Final[Records] = Records(kept=False, directory=None)

CHOICE: Final[Choice] = Choice(
    game=GameName.PASSING.value,
    players=PLAYERS,
    decks=ONE_DECK,
    conclusion=Conclusion(rounds=ROUNDS),
)


def a_room(table: str) -> RoomRecord:
    """One room as a lobby writes it down, gathered under the name given and settled by nobody yet."""
    return RoomRecord(
        table=table,
        code=CODE,
        choice=CHOICE,
        host=None,
        democratic=True,
        seats={},
        tints={},
        tokens={},
        ready={},
        seated={},
        revision=FIRST_REVISION,
        dealt=False,
        closed=False,
        reason=None,
    )


def a_ledger_at(store: Path) -> Ledger:
    """A store on disk at that directory, taken for this test the way a run takes its own."""
    return Ledger(store, NO_PATIENCE)


def a_written_room(store: Path, table: str) -> Ledger:
    """A store holding one room, handed back still held so a test goes on writing to it."""
    ledger = a_ledger_at(store)
    ledger.remember_room(a_room(table))
    return ledger


def only(kept: tuple[Kept, ...]) -> Kept:
    """The one record a store holds, which is what a test reading a single table back asks for."""
    (one,) = kept
    return one


def a_second_run(store: Path, ledger: Ledger) -> tuple[Kept, ...]:
    """Everything a fresh run over the same directory reads back, once the run that wrote it has let go."""
    ledger.close()
    reading = a_ledger_at(store)
    kept = reading.kept()
    reading.close()
    return kept


@dataclass(frozen=True)
class Naming(Case):
    """One name a table might be written down under, whatever the doors ahead of the store admit."""

    table: str


NAMED: Final[tuple[Naming, ...]] = (
    Naming(description="a name climbing out of wherever it is written", table="../../escape"),
    Naming(description="a name reading from the root of the machine", table="/tmp/pwned"),
    Naming(description="a name reading through a Windows directory", table="a\\b"),
    Naming(description="a name that is one step up and nothing else", table=".."),
    Naming(description="a name that is where it already stands", table="."),
    Naming(description="a name holding nothing but space", table="   "),
    Naming(description="a name written in characters no path reads plainly", table="☃☃"),
    Naming(description="a name a person would write", table=TABLE),
)


@pytest.mark.parametrize("case", NAMED, ids=descriptions(NAMED))
def test_a_table_is_written_down_inside_the_store_whatever_it_is_named(case: Naming, tmp_path: Path) -> None:
    """The store trusts no name, so what reaches it names one directory of the store and nowhere else."""
    written = tmp_path / a_directory_name(case.table)

    assert written.parent == tmp_path
    assert written.resolve().parent == tmp_path.resolve()


def test_two_names_that_read_alike_are_written_down_apart() -> None:
    """A slug is for whoever comes to look, and the mark beside it is what one directory is told apart by."""
    assert a_directory_name("Green Baize") != a_directory_name("green/baize")


def test_a_name_is_written_down_under_a_directory_a_person_would_look_for() -> None:
    assert a_directory_name(TABLE).startswith(f"{TABLE}-")


def test_a_room_is_written_down_where_this_account_alone_reads_it(tmp_path: Path) -> None:
    """The record names every card every seat is holding, and a sealed table is one the table alone reads."""
    ledger = a_written_room(tmp_path, TABLE)
    ledger.open_journal(TABLE, AN_ORIGIN)
    ledger.append(TABLE, A_COMMIT)
    directory = tmp_path / a_directory_name(TABLE)

    assert S_IMODE(directory.stat().st_mode) == DIRECTORY_MODE
    for name in (ROOM_FILE, ORIGIN_FILE, JOURNAL_FILE):
        assert S_IMODE((directory / name).stat().st_mode) == FILE_MODE

    ledger.close()


def test_a_room_written_down_reads_back_as_the_room_it_was(tmp_path: Path) -> None:
    ledger = a_written_room(tmp_path, TABLE)

    kept = only(a_second_run(tmp_path, ledger))

    assert kept.room == a_room(TABLE)
    assert kept.table is None


def test_a_room_written_down_twice_stands_as_it_was_written_last(tmp_path: Path) -> None:
    ledger = a_written_room(tmp_path, TABLE)
    settled = a_room(TABLE).model_copy(update={"revision": 4, "seats": {"Ada": 0}})
    ledger.remember_room(settled)

    assert only(a_second_run(tmp_path, ledger)).room == settled


def test_a_table_written_down_reads_back_holding_every_commit_that_landed_on_it(tmp_path: Path) -> None:
    ledger = a_written_room(tmp_path, TABLE)
    ledger.open_journal(TABLE, AN_ORIGIN)
    ledger.append(TABLE, A_COMMIT)
    ledger.append(TABLE, ANOTHER_COMMIT)

    kept = only(a_second_run(tmp_path, ledger))

    assert kept.table is not None
    assert kept.table.origin == AN_ORIGIN
    assert kept.table.commits == (A_COMMIT, ANOTHER_COMMIT)


def test_a_commit_written_down_after_a_restart_is_laid_after_the_lines_already_there(tmp_path: Path) -> None:
    """The path a table read back writes through, which opened no journal of its own in this run."""
    first = a_written_room(tmp_path, TABLE)
    first.open_journal(TABLE, AN_ORIGIN)
    first.append(TABLE, A_COMMIT)
    first.close()

    second = a_ledger_at(tmp_path)
    second.append(TABLE, ANOTHER_COMMIT)

    kept = only(a_second_run(tmp_path, second))
    assert kept.table is not None
    assert kept.table.commits == (A_COMMIT, ANOTHER_COMMIT)


def test_a_last_commit_a_run_was_cut_off_in_the_middle_of_is_dropped(tmp_path: Path) -> None:
    """The shape a killed process leaves, where the lines before it are a record of the table in themselves."""
    ledger = a_written_room(tmp_path, TABLE)
    ledger.open_journal(TABLE, AN_ORIGIN)
    ledger.append(TABLE, A_COMMIT)
    ledger.close()
    journal = tmp_path / a_directory_name(TABLE) / JOURNAL_FILE
    journal.write_text(f"{A_COMMIT}\n{A_TORN_COMMIT}", encoding="utf-8")

    reading = a_ledger_at(tmp_path)
    kept = only(reading.kept())
    reading.close()

    assert kept.table is not None
    assert kept.table.commits == (A_COMMIT,)


def test_a_commit_written_down_after_a_kill_is_laid_where_the_last_whole_line_ended(tmp_path: Path) -> None:
    """The pair a part-written line and the line after it would make reads as no commit and stands mid-record.

    A reader passes over the tail a kill leaves, so a writer that laid its next line after it would put a
    line nothing reads in the middle of the record and the whole table would be set aside at the restart
    after this one. The rule both keep is that a line counts once its newline is down.
    """
    ledger = a_written_room(tmp_path, TABLE)
    ledger.open_journal(TABLE, AN_ORIGIN)
    ledger.append(TABLE, A_COMMIT)
    ledger.close()
    journal = tmp_path / a_directory_name(TABLE) / JOURNAL_FILE
    journal.write_text(f"{A_COMMIT}\n{A_TORN_COMMIT}", encoding="utf-8")

    second = a_ledger_at(tmp_path)
    second.append(TABLE, ANOTHER_COMMIT)

    kept = only(a_second_run(tmp_path, second))
    assert kept.table is not None
    assert kept.table.commits == (A_COMMIT, ANOTHER_COMMIT)


def test_a_record_torn_where_a_record_is_never_torn_is_read_as_no_record() -> None:
    with pytest.raises(RecordUnread):
        whole_lines(f"{A_TORN_COMMIT}\n{A_COMMIT}\n", TABLE)


def test_a_record_this_run_makes_nothing_of_is_set_aside_and_the_rest_are_read(tmp_path: Path) -> None:
    ledger = a_written_room(tmp_path, TABLE)
    ledger.remember_room(a_room(ANOTHER_TABLE))
    ledger.close()
    unread = tmp_path / a_directory_name(ANOTHER_TABLE)
    (unread / ROOM_FILE).write_text(NOT_A_ROOM, encoding="utf-8")

    reading = a_ledger_at(tmp_path)
    kept = only(reading.kept())
    reading.close()

    assert kept.room.table == TABLE
    assert not unread.is_dir()
    assert unread.with_name(f"{unread.name}{SET_ASIDE}").is_dir()


def test_a_record_written_down_in_a_shape_this_run_reads_no_more_is_set_aside(tmp_path: Path) -> None:
    """What a build whose models have moved on finds, which is the whole reason a record states its version."""
    ledger = a_written_room(tmp_path, TABLE)
    ledger.close()
    room = tmp_path / a_directory_name(TABLE) / ROOM_FILE
    newer = {**loads(a_room(TABLE).model_dump_json()), "version": RECORD_VERSION + 1}
    room.write_text(dumps(newer), encoding="utf-8")

    reading = a_ledger_at(tmp_path)
    kept = reading.kept()
    reading.close()

    assert kept == ()


def test_a_record_a_run_sets_aside_stays_on_disk_under_a_name_it_passes_over(tmp_path: Path) -> None:
    """What a host does with a record naming rules it no longer holds, since a record is nobody's to destroy."""
    ledger = a_written_room(tmp_path, TABLE)

    ledger.set_aside(TABLE)

    directory = tmp_path / a_directory_name(TABLE)
    assert not directory.is_dir()
    assert (directory.with_name(f"{directory.name}{SET_ASIDE}") / ROOM_FILE).is_file()
    assert a_second_run(tmp_path, ledger) == ()


def test_a_forgotten_record_leaves_no_directory_behind_it(tmp_path: Path) -> None:
    ledger = a_written_room(tmp_path, TABLE)
    ledger.open_journal(TABLE, AN_ORIGIN)

    ledger.forget(TABLE)

    assert not (tmp_path / a_directory_name(TABLE)).is_dir()
    assert a_second_run(tmp_path, ledger) == ()


def test_a_store_is_held_by_the_one_run_writing_it(tmp_path: Path) -> None:
    """Two runs over one store leave a record neither of them reads back, so the second waits or runs nowhere."""
    ledger = a_ledger_at(tmp_path)

    with pytest.raises(StoreTaken):
        a_ledger_at(tmp_path)

    ledger.close()
    a_ledger_at(tmp_path).close()


def test_a_store_stands_open_to_this_account_alone(tmp_path: Path) -> None:
    store = tmp_path / "records"
    ledger = Ledger(store, NO_PATIENCE)

    assert S_IMODE(store.stat().st_mode) == DIRECTORY_MODE

    ledger.close()


def test_a_run_keeping_nothing_writes_no_directory_at_all(tmp_path: Path) -> None:
    """What a checkout being played with holds, which leaves the store a question the deployment answers."""
    assert a_ledger(NOTHING_KEPT) is FORGETFUL
    assert list(tmp_path.iterdir()) == []


def test_a_run_naming_no_directory_writes_to_the_records_of_the_checkout() -> None:
    assert KEPT.directory is None
    assert RECORDS.parent == REPOSITORY


def test_a_room_holding_the_company_reads_back_holding_them(tmp_path: Path) -> None:
    """The record a restart is the point of, read the whole way back off the disk it was written to."""
    ledger = a_ledger_at(tmp_path)
    settled = a_room(TABLE).model_copy(
        update={
            "seats": {"Ada": 0, "Grace": 1},
            "tints": {"Ada": Tint.ROSE, "Grace": Tint.TEAL},
            "ready": {"Ada": True, "Grace": True},
            "seated": {0: Seated(name="Ada", tint=Tint.ROSE)},
            "dealt": True,
            "revision": 9,
        }
    )
    ledger.remember_room(settled)

    assert only(a_second_run(tmp_path, ledger)).room == settled
