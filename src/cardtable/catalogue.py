from collections.abc import Mapping
from logging import Logger, getLogger
from random import Random
from time import monotonic, time
from typing import Final

from cardgames.backend.climbing.game import ClimbingGame
from cardgames.backend.climbing.state import ClimbingState
from cardgames.backend.passing.game import PassingGame
from cardgames.backend.passing.state import PassingState
from cardgames.backend.shedding.game import SheddingGame
from cardgames.backend.shedding.state import SheddingState
from cardgames.backend.showdown.game import ShowdownGame
from cardgames.backend.showdown.state import ShowdownState
from cardgames.frontend.climbing.layout import CLIMBING_SCENE
from cardgames.frontend.passing.layout import PASSING_SCENE
from cardgames.frontend.shedding.layout import SHEDDING_SCENE
from cardgames.frontend.showdown.layout import SHOWDOWN_SCENE
from cardserver.advanced import Advanced
from cardserver.gathering.gatherings import Gatherings
from cardserver.gathering.governed_say import GovernedSay
from cardserver.gathering.turnstile import Turnstile
from cardserver.naming.named import Named
from cardserver.naming.seated import Seated
from cardserver.protocols.presentation import Presentation
from cardserver.protocols.table import Table, TableId
from cardserver.registry import TableRegistry
from cardserver.remembering import Kept, Remembering, RoomRecord, TableRecord
from cardserver.schemas.choice import Choice
from cardserver.schemas.offering import Offering
from cardtable.admin import Admin
from cardtable.artwork import Artwork
from cardtable.games import GameName
from cardtable.hosting import Hosted, serve
from cardtable.records import Recorded, Records, a_ledger
from cardtable.settings import Settings
from cardwork.decks.deck import Deck
from cardwork.decks.standard import ONE_DECK, standard_decks
from cardwork.exceptions import GameValidationError
from cardwork.games.game import Game
from cardwork.states.state import GameState

LOGGER: Final[Logger] = getLogger("cardtable")
SECONDS_AN_HOUR: Final[float] = 3600.0
SEPARATOR: Final[str] = "\x00"
UNCOMMITTED: Final[int] = 0
TWO_DECKS: Final[int] = 2
ONE_DECK_ONLY: Final[tuple[int, ...]] = (ONE_DECK,)
ONE_DECK_OR_TWO: Final[tuple[int, ...]] = (ONE_DECK, TWO_DECKS)

OFFERINGS: Final[tuple[Offering, ...]] = (
    Offering(
        game=GameName.CLIMBING.value,
        title=CLIMBING_SCENE.title,
        seats=ClimbingGame.capacity,
        decks=ONE_DECK_OR_TWO,
    ),
    Offering(
        game=GameName.PASSING.value,
        title=PASSING_SCENE.title,
        seats=PassingGame.capacity,
        decks=ONE_DECK_OR_TWO,
    ),
    Offering(
        game=GameName.SHOWDOWN.value,
        title=SHOWDOWN_SCENE.title,
        seats=ShowdownGame.capacity,
        decks=ONE_DECK_ONLY,
    ),
    Offering(
        game=GameName.SHEDDING.value,
        title=SHEDDING_SCENE.title,
        seats=SheddingGame.capacity,
        decks=ONE_DECK_ONLY,
    ),
)


def a_jokered_deck(decks: int) -> Deck:
    """The decks chosen with a joker of either colour in each of them, which a game reading one is dealt from."""
    return standard_decks(
        decks,
        black_jokers=decks,
        red_jokers=decks,
    )


def a_generator(seed: int, table: TableId, head: int) -> Random:
    """The generator one table draws with: the seed the run states, the table's own name, and how far it has got.

    A run holds one seed and every table it deals is dealt from it, so the name of the table is drawn in
    beside it: two tables of one run draw from streams of their own, and a company that has played a hand at
    one of them knows nothing of what the next is dealt.

    How far the record goes is drawn in as well, which is what a table taken up again draws onward from. A
    match resumed from where its last commit left it stands where its generator has already been, so a stream
    reading from the record's length is a stream no run has drawn from at that table: the round dealt after a
    restart is a round of its own rather than the round the company has just played.

    The three are read as one word, so a run stating the seed it announced deals the match it dealt.
    """
    return Random(f"{seed}{SEPARATOR}{table}{SEPARATOR}{head}")


def a_passing_match(choice: Choice, generator: Random) -> PassingGame:
    """A match of `passing` over the decks chosen, each with a joker of either colour its rules read a win through."""
    return PassingGame(
        players=choice.players,
        deck=a_jokered_deck(choice.decks),
        conclusion=choice.conclusion,
        rng=generator,
    )


def a_showdown_match(choice: Choice, generator: Random) -> ShowdownGame:
    """A match of `showdown` over the decks chosen, ending where the company settled it does."""
    return ShowdownGame(
        players=choice.players,
        deck=standard_decks(choice.decks),
        conclusion=choice.conclusion,
        rng=generator,
    )


def a_shedding_match(choice: Choice, generator: Random) -> SheddingGame:
    """A match of `shedding` over the decks chosen, ending where the company settled it does."""
    return SheddingGame(
        players=choice.players,
        deck=standard_decks(choice.decks),
        conclusion=choice.conclusion,
        rng=generator,
    )


def a_climbing_match(choice: Choice, generator: Random) -> ClimbingGame:
    """A match of `climbing` over the decks chosen, ending where the company settled it does."""
    return ClimbingGame(
        players=choice.players,
        deck=standard_decks(choice.decks),
        conclusion=choice.conclusion,
        rng=generator,
    )


class Deals:
    """How a choice one gathering settled becomes a table in service, which is this host's own business.

    A gathering settles what is played while holding the name of no game, so what reaches here is a name, a
    seating, a count of decks and an ending, and this is where the rules of that name are found and dealt from
    the deck they are written for. The table lands in the registry the application already serves, so a deal
    leaves it answering under the name its company gathered at.

    The seed comes from the table rather than from the choice, which is what lets a run deal the match it dealt
    before whatever the company settles this time. Each table draws from a stream of its own all the same, so
    one run deals every table it holds a hand nobody at another has seen.

    A table is taken up here as well as dealt here, since the rules a record was written by are found by the
    name the record carries and this is where a name becomes rules.
    """

    def __init__(
        self,
        registry: TableRegistry,
        seed: int,
    ) -> None:
        self._registry = registry
        self._seed = seed

    def open(
        self,
        table: TableId,
        choice: Choice,
        seated: Mapping[int, Seated],
    ) -> None:
        """Deal the table one gathering settled on and put it into service under that name.

        Args:
            table: the name the table is served under, which is the one its gathering stands for.
            choice: what the company settled to play.
            seated: the name and tint each seat is read by, which the plaques of the table's layout carry.

        Raises:
            GameValidationError: when the rules refuse the table or the deck the choice asks for.
        """
        generator = a_generator(self._seed, table, UNCOMMITTED)
        match GameName(choice.game):
            case GameName.CLIMBING:
                self._put_into_service(
                    table,
                    a_climbing_match(choice, generator),
                    CLIMBING_SCENE,
                    seated,
                    cues=choice.cues,
                )

            case GameName.PASSING:
                self._put_into_service(
                    table,
                    a_passing_match(choice, generator),
                    PASSING_SCENE,
                    seated,
                    cues=choice.cues,
                )

            case GameName.SHOWDOWN:
                self._put_into_service(
                    table,
                    a_showdown_match(choice, generator),
                    SHOWDOWN_SCENE,
                    seated,
                    cues=choice.cues,
                )

            case GameName.SHEDDING:
                self._put_into_service(
                    table,
                    a_shedding_match(choice, generator),
                    SHEDDING_SCENE,
                    seated,
                    cues=choice.cues,
                )

    def resume(self, room: RoomRecord, record: TableRecord) -> None:
        """Take one table back up from the record kept of it and put it into service where its last commit left it.

        The rules are built the way they were built the first time and then handed the record, which is what
        makes a table taken up the table it was: the position before the first commit follows from the seating,
        the deck and the ending, so a record opening at it is the record of a table of exactly this shape.

        Args:
            room: the room the table was gathered in, which names the game, the seating and the plaques.
            record: everything written down of the table since it was dealt.

        Raises:
            ValueError: when the record names a game this host holds the rules of nowhere, or when a line of
                it was written for a cursor of another shape than the rules of that name declare.
            GameValidationError: when the rules refuse the table the record was written at, or when the record
                opens at an origin no table of this shape continues.
            RuntimeError: when what the rules were left owing carries the table round in a circle.
            TableTaken: when a table of that name is already in service.
        """
        choice = room.choice
        generator = a_generator(self._seed, room.table, len(record.commits))
        match GameName(choice.game):
            case GameName.CLIMBING:
                self._take_up(
                    room,
                    a_climbing_match(choice, generator),
                    Recorded[ClimbingState].read(record),
                    CLIMBING_SCENE,
                )

            case GameName.PASSING:
                self._take_up(
                    room,
                    a_passing_match(choice, generator),
                    Recorded[PassingState].read(record),
                    PASSING_SCENE,
                )

            case GameName.SHOWDOWN:
                self._take_up(
                    room,
                    a_showdown_match(choice, generator),
                    Recorded[ShowdownState].read(record),
                    SHOWDOWN_SCENE,
                )

            case GameName.SHEDDING:
                self._take_up(
                    room,
                    a_shedding_match(choice, generator),
                    Recorded[SheddingState].read(record),
                    SHEDDING_SCENE,
                )

    def _take_up[StateT: GameState](
        self,
        room: RoomRecord,
        game: Game[StateT],
        recorded: Recorded[StateT],
        presentation: Presentation,
    ) -> None:
        """Hand one game the record kept of it, settle what it was left owing, and put it back into service.

        The window a move opens belongs to the process that opened it, so a table cut off inside one is taken
        up owing whatever that window would have committed. Settling here is what commits it: the window has
        passed by the time a process has started, the rules need no loop to be asked what they owe, and what
        they answer is written down as the table opens.
        """
        game.resume(recorded.journal)
        settled = game.settle()
        self._registry.reopen(
            room.table,
            game,
            Named(
                presentation,
                room.seated,
                cues=room.choice.cues,
            ),
            applied=recorded.applied,
            settled=settled,
        )

    def _put_into_service[StateT: GameState](
        self,
        table: TableId,
        game: Table[StateT],
        presentation: Presentation,
        seated: Mapping[int, Seated],
        *,
        cues: bool = True,
    ) -> None:
        """Open one dealt game under a name, read through its arrangement as its seats were taken and lit."""
        self._registry.open(
            table,
            game,
            Named(
                presentation,
                seated,
                cues=cues,
            ),
        )


def collected(kept: Kept, retain_hours: float, now: float) -> bool:
    """Whether one record has stood unwritten longer than a run keeps one, which is what a restart clears away."""
    return now - kept.updated > retain_hours * SECONDS_AN_HOUR


def taken_up(
    keeping: Remembering,
    gatherings: Gatherings,
    deals: Deals,
    kept: Kept,
) -> None:
    """One record read back into a run's lobby: the room a company gathered in, and the table it became.

    The room comes first, since a token holds its seat through the room it was minted at and every route a
    table is played at reads that seat off it. A journal is the mark a deal leaves, so a record holding one is
    the record of a table dealt whatever the room says of itself, and a room whose journal stands nowhere
    gathers again as the room it was before the cards came out.

    A record this run makes nothing of stops at the table it belongs to: serving the tables a run does read
    beats answering for none of them over one record. It is set aside before the room it gathered is dropped,
    so what a run passes over stays on disk under a name of its own for whoever comes to look.
    """
    table = kept.room.table
    try:
        gatherings.restore(kept.room, dealt=kept.table is not None)
        if kept.table is not None:
            deals.resume(kept.room, kept.table)
    except (GameValidationError, ValueError, RuntimeError) as unread:
        LOGGER.warning("The record of table %r is set aside: %s", table, unread)
        keeping.set_aside(table)
        gatherings.drop(table)


def restored(
    keeping: Remembering,
    gatherings: Gatherings,
    deals: Deals,
    *,
    retain_hours: float,
    now: float,
) -> None:
    """Gather this run's lobby from what an earlier one wrote down, and collect the records nobody came back to.

    A run reads its store once, as it starts and before it answers anything, so a company opening the address
    they were handed finds the room they were in and the table they were at.

    A record older than a run keeps one is cleared away here and nowhere else. The clocks a reaper counts by
    start with the process, so a restart finds every table young; this is the one moment the store is weighed
    against a calendar, which is what keeps a host started and stopped around its own traffic to the size of
    the tables being played at it.
    """
    for kept in keeping.kept():
        if collected(kept, retain_hours, now):
            LOGGER.info("The record of table %r has stood unwritten too long, and it is cleared away", kept.room.table)
            keeping.forget(kept.room.table)
            continue

        taken_up(keeping, gatherings, deals, kept)


def opened(
    settings: Settings,
    choice: Choice,
    artwork: Artwork,
    advanced: Advanced,
    admin: Admin,
    *,
    records: Records,
) -> Hosted:
    """The table this run gathers: what it offers, the choice it stands at, and the service carrying both.

    This is the one place a game and a transport meet, and the one module of the whole repository naming
    `cardgames`: the rules, the scene they are read through, what a company may settle among and the adapter
    serving all of it come together here and nowhere else, which is what leaves each of them ignorant of the
    rest. The artwork travels through untouched, since which cards a table is drawn with is the same question
    whichever game it plays.

    Every guest holding a seat holds a say, which is the whole of what a table among friends asks, and a code
    guessed at costs the address it came from its allowance off the machine's own clock, at the window and the
    count the run is tuned to.

    The store is read before the run answers anything: the rooms an earlier one gathered and the tables they
    became come back as they were written down, and the run gathers its own only where nothing of that name
    stands. That is what carries a company across the moment the process serving them ends.

    Raises:
        StoreTaken: when another run still holds the store this one writes its tables to.
        GameValidationError: when the choice the run opens at names a game offered nowhere, a table that game
            seats nowhere, or a count of decks it is dealt from nowhere.
    """
    keeping = a_ledger(records)
    registry = TableRegistry(settings.grace_seconds, keeping=keeping)
    deals = Deals(registry, settings.seed)
    gatherings = Gatherings(
        deals,
        offerings=OFFERINGS,
        say=GovernedSay(),
        turnstile=Turnstile.watching(
            monotonic,
            window=advanced.turnstile_window,
            wrong_codes_allowed=advanced.wrong_codes_allowed,
        ),
        keeping=keeping,
        clock=monotonic,
        presence_stands=advanced.presence_stands,
    )
    restored(
        keeping,
        gatherings,
        deals,
        retain_hours=records.retain_hours,
        now=time(),
    )
    return serve(
        registry,
        gatherings,
        settings,
        choice,
        artwork,
        keeping=keeping,
        advanced=advanced,
        admin=admin,
    )
