from dataclasses import dataclass
from typing import Final

import pytest

from cardgames.backend.climbing.game import ClimbingGame
from cardgames.backend.passing.game import PassingGame
from cardgames.backend.shedding.game import SheddingGame
from cardgames.backend.showdown.game import ShowdownGame
from cardgames.frontend.climbing.layout import CLIMBING_SCENE
from cardgames.frontend.passing.layout import PASSING_SCENE
from cardgames.frontend.shedding.layout import SHEDDING_SCENE
from cardgames.frontend.showdown.layout import SHOWDOWN_SCENE
from cardserver.registry import TableRegistry
from cardserver.remembering import FORGETFUL
from cardserver.schemas import Offering
from cardtable.catalogue import OFFERINGS, Deals
from cardtable.games import GAMES_HELD, GameName
from cardwork.exceptions import GameValidationError
from cardwork.games.capacity import Capacity
from tests.cases import Case, descriptions

from .tables import NO_GRACE, SEED, TABLE, a_seated_company, settled

SEATINGS: Final[dict[str, Capacity]] = {
    GameName.CLIMBING.value: ClimbingGame.capacity,
    GameName.PASSING.value: PassingGame.capacity,
    GameName.SHOWDOWN.value: ShowdownGame.capacity,
    GameName.SHEDDING.value: SheddingGame.capacity,
}

TITLES: Final[dict[str, str]] = {
    GameName.CLIMBING.value: CLIMBING_SCENE.title,
    GameName.PASSING.value: PASSING_SCENE.title,
    GameName.SHOWDOWN.value: SHOWDOWN_SCENE.title,
    GameName.SHEDDING.value: SHEDDING_SCENE.title,
}


@dataclass(frozen=True)
class DealCase(Case):
    """One table a host offers: the game, how many decks it is dealt from, and how many seats it holds."""

    game: str
    decks: int
    seats: int


DEALS: Final[tuple[DealCase, ...]] = tuple(
    DealCase(
        description=f"{offering.title.lower()} from {decks} deck at {seats} seats",
        game=offering.game,
        decks=decks,
        seats=seats,
    )
    for offering in OFFERINGS
    for decks in offering.decks
    for seats in range(offering.seats.least, offering.seats.most + 1)
)


def _is_dealt(case: DealCase) -> bool:
    """Whether the rules deal the table one offered case asks for, which is what a company meets at the deal."""
    tables = TableRegistry(NO_GRACE, keeping=FORGETFUL)
    try:
        Deals(tables, SEED).open(
            TABLE, settled(GameName(case.game), case.seats, case.decks), a_seated_company(case.seats)
        )
    except GameValidationError:
        return False

    return True


def test_a_host_offers_every_game_it_holds_the_rules_of() -> None:
    assert tuple(offering.game for offering in OFFERINGS) == GAMES_HELD


@pytest.mark.parametrize("offering", OFFERINGS, ids=[offering.game for offering in OFFERINGS])
def test_a_game_is_offered_at_the_tables_its_own_rules_seat(offering: Offering) -> None:
    """The seating a company chooses among is the game's own declaration rather than a second reading of it."""
    assert offering.seats == SEATINGS[offering.game]


@pytest.mark.parametrize("offering", OFFERINGS, ids=[offering.game for offering in OFFERINGS])
def test_a_game_is_offered_under_the_title_its_own_scene_states(offering: Offering) -> None:
    """A page names a game by what it is offered under, which is the title the felt is drawn with."""
    assert offering.title == TITLES[offering.game]


@pytest.mark.parametrize("case", DEALS, ids=descriptions(DEALS))
def test_a_table_a_host_offers_is_dealt_or_refused_in_words(case: DealCase) -> None:
    """What is on offer and what the rules deal are two statements, and this is what holds them together.

    Every table an offering promises is settled here — each count of decks at each seating it names — and every
    one of them either deals or is refused with a sentence a company can act on. A game holds the last word,
    since a seating and a count of decks state something apart and a rule may turn on both: `climbing` reads a
    hand of at most twenty-six cards, so two decks halved between two seats are refused where they are asked
    for. What this rules out is the third answer — a promise that hangs, or one the server meets with a defect.
    """
    tables = TableRegistry(NO_GRACE, keeping=FORGETFUL)
    choice = settled(GameName(case.game), case.seats, case.decks)

    try:
        Deals(tables, SEED).open(TABLE, choice, a_seated_company(case.seats))
    except GameValidationError as refusal:
        assert str(refusal).strip()
        return

    assert tables.session(TABLE).head > 0


@pytest.mark.parametrize("offering", OFFERINGS, ids=[offering.game for offering in OFFERINGS])
def test_every_count_of_decks_a_host_offers_is_dealt_at_some_table_the_game_seats(offering: Offering) -> None:
    """A count of decks named nowhere it is dealt would be an offer standing for nothing at all."""
    for decks in offering.decks:
        assert any(
            case.game == offering.game and case.decks == decks and _is_dealt(case)
            for case in DEALS
            if case.game == offering.game
        )
