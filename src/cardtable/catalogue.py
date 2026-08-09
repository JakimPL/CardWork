from collections.abc import Mapping
from random import Random
from time import monotonic
from typing import Final

from cardgames.backend.climbing.game import ClimbingGame
from cardgames.backend.passing.game import PassingGame
from cardgames.backend.shedding.game import SheddingGame
from cardgames.backend.showdown.game import ShowdownGame
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
from cardserver.schemas.choice import Choice
from cardserver.schemas.offering import Offering
from cardtable.admin import Admin
from cardtable.artwork import Artwork
from cardtable.games import GameName
from cardtable.hosting import Hosted, serve
from cardtable.settings import Settings
from cardwork.decks.deck import Deck
from cardwork.decks.standard import ONE_DECK, standard_decks
from cardwork.states.state import GameState

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


def a_passing_match(choice: Choice, seed: int) -> PassingGame:
    """A match of `passing` over the decks chosen, each with a joker of either colour its rules read a win through."""
    return PassingGame(
        players=choice.players,
        deck=a_jokered_deck(choice.decks),
        conclusion=choice.conclusion,
        rng=Random(seed),
    )


def a_showdown_match(choice: Choice, seed: int) -> ShowdownGame:
    """A match of `showdown` over the decks chosen, ending where the company settled it does."""
    return ShowdownGame(
        players=choice.players,
        deck=standard_decks(choice.decks),
        conclusion=choice.conclusion,
        rng=Random(seed),
    )


def a_shedding_match(choice: Choice, seed: int) -> SheddingGame:
    """A match of `shedding` over the decks chosen, ending where the company settled it does."""
    return SheddingGame(
        players=choice.players,
        deck=standard_decks(choice.decks),
        conclusion=choice.conclusion,
        rng=Random(seed),
    )


def a_climbing_match(choice: Choice, seed: int) -> ClimbingGame:
    """A match of `climbing` over the decks chosen, ending where the company settled it does."""
    return ClimbingGame(
        players=choice.players,
        deck=standard_decks(choice.decks),
        conclusion=choice.conclusion,
        rng=Random(seed),
    )


class Deals:
    """How a choice one gathering settled becomes a table in service, which is this host's own business.

    A gathering settles what is played while holding the name of no game, so what reaches here is a name, a
    seating, a count of decks and an ending, and this is where the rules of that name are found and dealt from
    the deck they are written for. The table lands in the registry the application already serves, so a deal
    leaves it answering under the name its company gathered at.

    The seed comes from the table rather than from the choice, which is what lets a run deal the match it dealt
    before whatever the company settles this time.
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
        match GameName(choice.game):
            case GameName.CLIMBING:
                self._put_into_service(
                    table,
                    a_climbing_match(choice, self._seed),
                    CLIMBING_SCENE,
                    seated,
                    cues=choice.cues,
                )

            case GameName.PASSING:
                self._put_into_service(
                    table,
                    a_passing_match(choice, self._seed),
                    PASSING_SCENE,
                    seated,
                    cues=choice.cues,
                )

            case GameName.SHOWDOWN:
                self._put_into_service(
                    table,
                    a_showdown_match(choice, self._seed),
                    SHOWDOWN_SCENE,
                    seated,
                    cues=choice.cues,
                )

            case GameName.SHEDDING:
                self._put_into_service(
                    table,
                    a_shedding_match(choice, self._seed),
                    SHEDDING_SCENE,
                    seated,
                    cues=choice.cues,
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


def opened(
    settings: Settings,
    choice: Choice,
    artwork: Artwork,
    advanced: Advanced,
    admin: Admin,
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

    Raises:
        GameValidationError: when the choice the run opens at names a game offered nowhere, a table that game
            seats nowhere, or a count of decks it is dealt from nowhere.
    """
    registry = TableRegistry(settings.grace_seconds)
    gatherings = Gatherings(
        Deals(registry, settings.seed),
        offerings=OFFERINGS,
        say=GovernedSay(),
        turnstile=Turnstile.watching(
            monotonic,
            window=advanced.turnstile_window,
            wrong_codes_allowed=advanced.wrong_codes_allowed,
        ),
        clock=monotonic,
        presence_stands=advanced.presence_stands,
    )
    return serve(
        registry,
        gatherings,
        settings,
        choice,
        artwork,
        advanced=advanced,
        admin=admin,
    )
