from random import Random
from typing import Final

import pytest

from cardserver.errors import TableTaken, UnknownTable
from cardserver.registry import TableRegistry
from cardserver.remembering import FORGETFUL
from cardserver.streams import STREAM_START, commits

from ..games.demo import DECK, SEATS, SealedRoundGame
from .company import Ticking
from .conftest import NO_GRACE, SEED, STREAM_PATIENCE, TABLE, UNSERVED
from .layout import SEALED_SCENE

IDLE: Final[float] = 3600.0


def another_table() -> SealedRoundGame:
    return SealedRoundGame(players=SEATS, deck=DECK, rng=Random(SEED))


def a_table_on(ticking: Ticking) -> TableRegistry:
    """One table in service, told the time by a clock a test moves by hand."""
    registry = TableRegistry(NO_GRACE, keeping=FORGETFUL, clock=ticking)
    registry.open(TABLE, another_table(), SEALED_SCENE)
    return registry


async def followed(registry: TableRegistry) -> None:
    """One stream taken up on the table and read to its end, as a page following the table does."""
    async for _ in commits(registry.session(TABLE), None, STREAM_START, STREAM_PATIENCE):
        pass


async def test_a_table_in_service_is_found_by_name(registry: TableRegistry) -> None:
    assert registry.session(TABLE).head > 0


async def test_a_table_out_of_service_is_named_in_the_refusal(registry: TableRegistry) -> None:
    with pytest.raises(UnknownTable):
        registry.session(UNSERVED)


async def test_a_name_already_in_service_is_left_as_it_was(registry: TableRegistry) -> None:
    with pytest.raises(TableTaken):
        registry.open(TABLE, another_table(), SEALED_SCENE)


async def test_tables_are_served_one_session_each(registry: TableRegistry) -> None:
    opened = registry.open("second-table", another_table(), SEALED_SCENE)

    assert registry.session("second-table") is opened
    assert opened is not registry.session(TABLE)


def test_a_registry_opens_holding_no_tables() -> None:
    registry = TableRegistry(NO_GRACE, keeping=FORGETFUL)

    with pytest.raises(UnknownTable):
        registry.session(TABLE)


async def test_a_table_nobody_has_come_back_to_falls_due_to_be_cleared() -> None:
    ticking = Ticking()
    registry = a_table_on(ticking)

    ticking.on(IDLE + 1.0)

    assert registry.idle(IDLE, ticking()) == (TABLE,)


async def test_a_table_somebody_is_following_stands_however_long_nobody_commits() -> None:
    """A company turning a hand over commits nothing while they think, and the page they think over says so."""
    ticking = Ticking()
    registry = a_table_on(ticking)
    ticking.on(IDLE + 1.0)

    await followed(registry)

    assert registry.idle(IDLE, ticking()) == ()
