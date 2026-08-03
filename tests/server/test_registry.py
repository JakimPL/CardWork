from random import Random

import pytest

from cardserver.errors import UnknownTable
from cardserver.registry import TableRegistry
from cardwork.states.state import GameState

from ..games.demo import DECK, SEATS, SealedRoundGame
from .conftest import NO_GRACE, SEED, TABLE, UNSERVED


def another_table() -> SealedRoundGame:
    return SealedRoundGame(players=SEATS, deck=DECK, rng=Random(SEED))


async def test_a_table_in_service_is_found_by_name(registry: TableRegistry[GameState]) -> None:
    assert registry.session(TABLE).head > 0


async def test_a_table_out_of_service_is_named_in_the_refusal(registry: TableRegistry[GameState]) -> None:
    with pytest.raises(UnknownTable):
        registry.session(UNSERVED)


async def test_a_name_already_in_service_is_left_as_it_was(registry: TableRegistry[GameState]) -> None:
    with pytest.raises(ValueError):
        registry.open(TABLE, another_table())


async def test_tables_are_served_one_session_each(registry: TableRegistry[GameState]) -> None:
    opened = registry.open("second-table", another_table())

    assert registry.session("second-table") is opened
    assert opened is not registry.session(TABLE)


def test_a_registry_opens_holding_no_tables() -> None:
    registry = TableRegistry[GameState](NO_GRACE)

    with pytest.raises(UnknownTable):
        registry.session(TABLE)
