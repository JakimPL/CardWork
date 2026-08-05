from collections.abc import Mapping

from cardwork.presentation.interlude import Interlude
from cardwork.presentation.readout import Readout
from cardwork.presentation.scope import Scope
from cardwork.rounds.state import MatchPhase, RoundState


def match_interludes() -> Mapping[str, Interlude]:
    """The two phases a match played in rounds pauses at, which is where `MatchPhase` leaves the table at rest.

    A round closed stands between rounds until the next is dealt, and a match decided stands over for good, so
    the two members of `MatchPhase` are exactly the two pauses a player reads a round game through. A game
    pausing somewhere of its own — a trick taken, a hand revealed — names that phase beside these.
    """
    return {
        MatchPhase.BETWEEN_ROUNDS: Interlude.ROUND,
        MatchPhase.MATCH_OVER: Interlude.MATCH,
    }


def match_phases() -> Mapping[str, str]:
    """The words a player reads the two phases of a match played in rounds by, which caption the pauses above.

    Every phase a table stands in takes a caption, and a layout is held to captioning the ones play pauses at,
    so the pair that states those pauses states the words for them as well. A game captions the stages of its
    own round beside these.
    """
    return {
        MatchPhase.BETWEEN_ROUNDS: "Between rounds",
        MatchPhase.MATCH_OVER: "Match over",
    }


def match_readouts(state: type[RoundState]) -> tuple[Readout, ...]:
    """The three figures every match played in rounds shows, read against the state that game is played with.

    The standing of record, what the round in play has scored so far, and which round that is: `RoundState`
    declares all three whatever game runs on it, and every game shows them under the same words. The state class
    arrives here so each name is read against the cursor the game actually carries, and a game states the figures
    that are its own — the rounds it runs to, the seat that went out — beside these.

    Args:
        state: the game's own state class, which the three names are read against.
    """
    return (
        Readout.of(state, "points", "Points", scope=Scope.SEAT),
        Readout.of(state, "round_points", "This round", scope=Scope.SEAT),
        Readout.of(state, "round_number", "Round", scope=Scope.TABLE),
    )
