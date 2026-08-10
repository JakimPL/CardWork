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
from cardserver.remembering import RoomRecord, TableRecord
from cardserver.schemas import Choice, Offering
from cardwork.games.capacity import Capacity
from cardwork.moves.actions import Play
from cardwork.moves.move import Move
from cardwork.rounds.conclusion import Conclusion

from ..games.demo import DECK, SealedRoundGame
from .keeping import Keeping, a_journal, applied_of
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
STREAM_PATIENCE: Final[float] = 0.5
PRESENCE_STANDS: Final[float] = 60.0

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


COMPANY: Final[tuple[str, ...]] = ("Ada", "Grace", "Alan")
FIRST_CARD: Final[frozenset[int]] = frozenset({0})


def a_sealing(seat: int) -> Move:
    """One seat sealing the first card of its hand in its own tray, which is the move this game is played by."""
    return Move(player=seat, action=Play(group="sealed", indices=FIRST_CARD))


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
        self.resumed: list[TableId] = []

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
            self._match(choice),
            Named(SEALED_SCENE, seated),
        )

    def resume(self, room: RoomRecord, record: TableRecord) -> None:
        """Take one table back up from the record kept of it, which is what a run does over what it wrote down.

        The rules are handed the record and stand where its last commit left them, and the keys the lines
        carry go to the session, so a retry crossing the restart is answered with the sequence it reached.
        Whatever the window a run was cut off inside would have committed is settled here and written down as
        the table opens, since a window belongs to the process that opened it.
        """
        game = self._match(room.choice)
        game.resume(a_journal(record))
        settled = game.settle()
        self.resumed.append(room.table)
        self._registry.reopen(
            room.table,
            game,
            Named(SEALED_SCENE, room.seated),
            applied=applied_of(record),
            settled=settled,
        )

    def _match(self, choice: Choice) -> SealedRoundGame:
        """A match of the demo game at the table the choice settled, dealt from the deck these tests play with."""
        return SealedRoundGame(
            players=choice.players,
            deck=DECK,
            rng=Random(DEALT_FROM),
        )


@dataclass(frozen=True)
class Rig:
    """One run under test: the tables it serves, the rooms it gathers, the store it writes to and its clock.

    A run gathering a fresh table and a run reading one back from a record hold the same things, so this is
    what both of them start from and a restart under test is a second rig over the store the first wrote to.

    The application carries the routes a table is played at as well, since a gathering is dealt into a table
    the same application answers for: reading a plaque after the deal is what shows a name reaching the felt.
    """

    registry: TableRegistry
    gatherings: Gatherings
    deals: Deals
    keeping: Keeping
    ticking: Ticking
    app: FastAPI


@dataclass(frozen=True)
class Gathered:
    """One table gathering under test, read together with the run that holds it."""

    registry: TableRegistry
    gatherings: Gatherings
    gathering: Gathering
    deals: Deals
    keeping: Keeping
    ticking: Ticking
    app: FastAPI


def a_rig(keeping: Keeping) -> Rig:
    """A run over one store, holding an empty lobby until a table is gathered at it or read back into it."""
    ticking = Ticking()
    registry = TableRegistry(NO_GRACE, keeping=keeping, clock=ticking)
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
        keeping=keeping,
        clock=ticking,
        presence_stands=PRESENCE_STANDS,
    )
    return Rig(
        registry=registry,
        gatherings=gatherings,
        deals=deals,
        keeping=keeping,
        ticking=ticking,
        app=create_app(
            registry,
            gatherings,
            gatherings,
            sweep_seconds=SWEEP_SECONDS,
            stream_patience=STREAM_PATIENCE,
        ),
    )


def at(rig: Rig, gathering: Gathering) -> Gathered:
    """One room of a run's lobby, read together with the run holding it."""
    return Gathered(
        registry=rig.registry,
        gatherings=rig.gatherings,
        gathering=gathering,
        deals=rig.deals,
        keeping=rig.keeping,
        ticking=rig.ticking,
        app=rig.app,
    )


def a_seated_company(gathered_at: Gathered) -> dict[str, str]:
    """The whole company arrived, seated in order and committed, and the token each of them speaks through."""
    gathering = gathered_at.gathering
    tokens = {name: gathering.admit(name) for name in COMPANY}
    for seat, name in enumerate(COMPANY):
        gathering.claim(name, seat, gathering.revision)

    for name in COMPANY:
        gathering.ready(name, True, gathering.revision)

    return tokens


def a_dealt_table(gathered_at: Gathered) -> dict[str, str]:
    """The table under test dealt into service, and the token each of the company plays through."""
    tokens = a_seated_company(gathered_at)
    gathered_at.gathering.deal(gathered_at.gathering.revision)
    return tokens


def gathered(table: TableId, players: int) -> Gathered:
    """One table gathering on its code, at a choice of the demo game seating that many."""
    rig = a_rig(Keeping())
    return at(
        rig,
        rig.gatherings.open(
            table,
            CODE,
            a_sealed_round(players),
            democratic=True,
        ),
    )


def restarted(gathered_at: Gathered) -> Rig:
    """A fresh run over everything an earlier one wrote down, holding the rooms and tables its records hold.

    This is the whole of a restart as the adapter meets it: nothing the first run held in memory carries over,
    only what its store was told, and the second run gathers its lobby from that. Rooms come back first and
    tables after, and a journal written down is the mark a deal left, whatever the room says of itself.
    """
    rig = a_rig(gathered_at.keeping)
    for kept in gathered_at.keeping.kept():
        rig.gatherings.restore(kept.room, dealt=kept.table is not None or kept.room.dealt)

    for kept in gathered_at.keeping.kept():
        if kept.table is not None:
            rig.deals.resume(kept.room, kept.table)

    return rig
