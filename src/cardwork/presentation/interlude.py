from enum import StrEnum


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
