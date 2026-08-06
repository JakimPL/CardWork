from collections.abc import Mapping
from enum import StrEnum

from cardwork.presentation.repeats import distinct


class Interlude(StrEnum):
    """A pause in play, held open for the players to read what the table has just come to.

    A boundary settles in a burst — the round scored into the standing, the cards gathered, the next hand dealt —
    so a player watching the screen alone reads a round giving way to a fresh one with nothing said about what it
    came to. A phase named as an interlude is one the interface stops at and reads out: `ROUND` is a round closed
    with the next still to open, and `MATCH` is a match played out.

    Which phases those are is a game's to state, since a game names the phases of its own rounds, and a match
    played through `cardwork.rounds` states the pair `presets.match_interludes` holds.
    """

    ROUND = "round"
    MATCH = "match"


def uncaptioned(
    interludes: Mapping[str, Interlude],
    phases: Mapping[str, str],
) -> str | None:
    """Which phase play pauses at the captions leave out, and None where every pause is captioned.

    A pause is held open for a player to read where play stands, which is the words the phase reads under, so a
    phase named as an interlude is one the captions hold. A `Layout` and the `Scene` it is drawn from are held to
    this one rule.

    Args:
        interludes: the phases play pauses at, each under the pause it is read as.
        phases: the words each phase of the game reads under.
    """
    missing = distinct(tuple(phase for phase in interludes if phase not in phases))
    if missing:
        return f"A phase play pauses at is captioned like any other, and these are not: {missing}"

    return None
