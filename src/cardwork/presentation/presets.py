from collections.abc import Mapping

from cardwork.presentation.interlude import Interlude
from cardwork.rounds.state import MatchPhase


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
