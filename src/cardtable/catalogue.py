from enum import StrEnum
from random import Random
from typing import Final

from cardgames.backend.passing.game import PassingGame
from cardgames.backend.showdown.game import ShowdownGame
from cardgames.frontend.passing.layout import PASSING_SCENE
from cardgames.frontend.showdown.layout import SHOWDOWN_SCENE
from cardtable.hosting import Hosted, serve
from cardtable.settings import Settings
from cardwork.decks.deck import Deck
from cardwork.decks.standard import standard_deck, standard_decks

ONE_DECK: Final[int] = 1
PASSING_DECK: Final[Deck] = standard_decks(ONE_DECK, black_jokers=1, red_jokers=1)
SHOWDOWN_DECK: Final[Deck] = standard_deck()


class GameName(StrEnum):
    """The games this host puts into service, each named as a person asks for one."""

    PASSING = "passing"
    SHOWDOWN = "showdown"


def a_passing_match(settings: Settings) -> PassingGame:
    """A match of `passing` over one deck with a joker of either colour, which its rules read a win through."""
    return PassingGame(players=settings.players, deck=PASSING_DECK, rng=Random(settings.seed))


def a_showdown_match(settings: Settings) -> ShowdownGame:
    """A match of `showdown` over one standard deck, running the rounds the settings ask of it."""
    return ShowdownGame(
        players=settings.players,
        deck=SHOWDOWN_DECK,
        rounds=settings.rounds,
        rng=Random(settings.seed),
    )


def opened(game: GameName, settings: Settings) -> Hosted:
    """The game named, dealt from the deck its rules are written for and put into service.

    This is the one place a game and a transport meet, and the one module of the whole repository naming
    `cardgames`: the rules, the scene they are read through and the adapter serving both come together here
    and nowhere else, which is what leaves each of the three ignorant of the other two.
    """
    match game:
        case GameName.PASSING:
            return serve(a_passing_match(settings), PASSING_SCENE, settings)

        case GameName.SHOWDOWN:
            return serve(a_showdown_match(settings), SHOWDOWN_SCENE, settings)
