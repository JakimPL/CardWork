from collections.abc import Mapping
from dataclasses import dataclass
from random import Random
from typing import Final

from fastapi import FastAPI

from cardserver.app import create_app
from cardserver.gathering import Gathering, Gatherings, GovernedSay, Turnstile
from cardserver.naming import Named, Seated
from cardserver.protocols import TableId
from cardserver.registry import TableRegistry
from cardserver.schemas import Choice, Offering
from cardwork.games.capacity import Capacity
from cardwork.rounds.conclusion import Conclusion

from ..games.demo import DECK, SealedRoundGame
from .layout import SEALED_SCENE, TITLE

GAME: Final[str] = "sealed"
OTHER_GAME: Final[str] = "unsealed"
OTHER_TITLE: Final[str] = "Unsealed round"
CODE: Final[str] = "KQAJ72"
WRONG_CODE: Final[str] = "234567"
COMPANY_LEAST: Final[int] = 2
COMPANY_MOST_HERE: Final[int] = 4
ONE_DECK: Final[int] = 1
TWO_DECKS: Final[int] = 2
ROUNDS: Final[int] = 1
NO_GRACE: Final[float] = 0.0
DEALT_FROM: Final[int] = 20260806
TURNSTILE_WINDOW: Final[float] = 60.0
WRONG_CODES_ALLOWED: Final[int] = 10
SWEEP_SECONDS: Final[float] = 60.0

OFFERINGS: Final[tuple[Offering, ...]] = (
    Offering(
        game=GAME,
        title=TITLE,
        seats=Capacity(least=COMPANY_LEAST, most=COMPANY_MOST_HERE),
        decks=(ONE_DECK,),
    ),
    Offering(
        game=OTHER_GAME,
        title=OTHER_TITLE,
        seats=Capacity(least=COMPANY_LEAST, most=COMPANY_MOST_HERE),
        decks=(ONE_DECK, TWO_DECKS),
    ),
)


def a_sealed_round(players: int) -> Choice:
    """A choice of the demo game at a table of that many seats, run to a single round."""
    return Choice(
        game=GAME,
        players=players,
        decks=ONE_DECK,
        conclusion=Conclusion(rounds=ROUNDS),
    )


class Ticking:
    """A clock a test moves by hand, which is what lets a window pass without a test waiting for it."""

    def __init__(self) -> None:
        self._now = 0.0

    def __call__(self) -> float:
        return self._now

    def on(self, seconds: float) -> None:
        """Move the clock forward, which is how long a test says has gone by."""
        self._now += seconds


class Deals:
    """An opening that deals the demo game, which is what a gathering at these tests becomes.

    What it was handed is kept as well as opened, so a test reads the seating a deal settled straight off it,
    and reads it through a layout where the point is that the names and tints reach one.
    """

    def __init__(self, registry: TableRegistry) -> None:
        self._registry = registry
        self.dealt: list[tuple[TableId, Choice, Mapping[int, Seated]]] = []

    def open(
        self,
        table: TableId,
        choice: Choice,
        seated: Mapping[int, Seated],
    ) -> None:
        """Deal the demo game at the table the choice settled, with its seats named and tinted."""
        self.dealt.append((table, choice, seated))
        self._registry.open(
            table,
            SealedRoundGame(
                players=choice.players,
                deck=DECK,
                rng=Random(DEALT_FROM),
            ),
            Named(SEALED_SCENE, seated),
        )


@dataclass(frozen=True)
class Gathered:
    """One table gathering under test: the lobby, the gathering itself, and the application serving both.

    The application carries the routes a table is played at as well, since a gathering is dealt into a table
    the same application answers for: reading a plaque after the deal is what shows a name reaching the felt.
    """

    registry: TableRegistry
    gatherings: Gatherings
    gathering: Gathering
    deals: Deals
    ticking: Ticking
    app: FastAPI


def gathered(table: TableId, players: int) -> Gathered:
    """One table gathering on its code, at a choice of the demo game seating that many."""
    ticking = Ticking()
    registry = TableRegistry(NO_GRACE, ticking)
    deals = Deals(registry)
    gatherings = Gatherings(
        deals,
        offerings=OFFERINGS,
        say=GovernedSay(),
        turnstile=Turnstile.watching(
            ticking,
            window=TURNSTILE_WINDOW,
            wrong_codes_allowed=WRONG_CODES_ALLOWED,
        ),
        clock=ticking,
    )
    return Gathered(
        registry=registry,
        gatherings=gatherings,
        gathering=gatherings.open(
            table,
            CODE,
            a_sealed_round(players),
            democratic=True,
        ),
        deals=deals,
        ticking=ticking,
        app=create_app(
            registry,
            gatherings,
            gatherings,
            sweep_seconds=SWEEP_SECONDS,
        ),
    )
