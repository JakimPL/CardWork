from collections.abc import Callable
from dataclasses import dataclass
from random import Random
from typing import Final

from cardgames.backend.passing.game import PassingGame
from cardgames.backend.passing.state import PassingPhase
from cardgames.backend.showdown.game import ShowdownGame
from cardgames.backend.showdown.state import ShowdownPhase
from cardgames.frontend.passing.layout import PASSING_SCENE
from cardgames.frontend.showdown.layout import SHOWDOWN_SCENE
from cardwork.decks.standard import standard_deck, standard_decks
from cardwork.games.game import Game
from cardwork.presentation.scene import Scene
from cardwork.rounds.state import MatchPhase
from cardwork.states.state import GameState

from ..cases import Case

PLAYERS: Final[int] = 3
SEED: Final[int] = 7
ROUNDS: Final[int] = 2

SEATS: Final[tuple[int, ...]] = tuple(range(PLAYERS))
OBSERVERS: Final[tuple[int | None, ...]] = SEATS + (None,)


@dataclass(frozen=True)
class LayoutCase(Case):
    """One game's layout beside a table of its own, and the whole of what an observer reads off it.

    The counts stand for what a layout holds rather than for what it looks like: how many zones an observer
    has of its own, how many the table shares, how many gestures a turn is made of, how many zones a plaque
    counts. `phases` is every phase the game's cursor may read, which the captions are held against.
    """

    scene: Scene
    table: Callable[[], Game[GameState]]
    held: int
    shared: int
    gestures: int
    counts: int
    phases: tuple[str, ...]


def a_passing_table() -> PassingGame:
    """A passing table of three seats, dealt from a deck holding a joker of each colour."""
    return PassingGame(
        players=PLAYERS,
        deck=standard_decks(1, black_jokers=1, red_jokers=1),
        rng=Random(SEED),
    )


def a_showdown_table() -> ShowdownGame:
    """A showdown table of three seats, dealt from one standard deck and built for two rounds."""
    return ShowdownGame(
        players=PLAYERS,
        deck=standard_deck(),
        rounds=ROUNDS,
        rng=Random(SEED),
    )


CASES: Final[tuple[LayoutCase, ...]] = (
    LayoutCase(
        description="passing lays out a hand against the pile and the stack",
        scene=PASSING_SCENE,
        table=a_passing_table,
        held=1,
        shared=2,
        gestures=2,
        counts=1,
        phases=tuple(PassingPhase) + tuple(MatchPhase),
    ),
    LayoutCase(
        description="showdown lays out two holdings and a tray against the stock and the revealed cards",
        scene=SHOWDOWN_SCENE,
        table=a_showdown_table,
        held=3,
        shared=2,
        gestures=2,
        counts=3,
        phases=tuple(ShowdownPhase) + tuple(MatchPhase),
    ),
)
