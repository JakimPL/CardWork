from collections.abc import Mapping
from secrets import choice, compare_digest
from typing import Final

from cardwork.cards.orders import RANK_SEQUENCE
from cardwork.cards.rank import Rank, Ranks

CODE_LENGTH: Final[int] = 6
SEPARATORS: Final[str] = " -_"
APART: Final[str] = " "

READ_AS: Final[Mapping[str, Rank]] = {rank.value: rank for rank in RANK_SEQUENCE}
LONGEST_RANK: Final[int] = max(len(rank.value) for rank in RANK_SEQUENCE)


def a_drawn_code() -> str:
    """A join code drawn at random, which is the hand of ranks one table is entered by.

    The draw comes from the system's own source of randomness rather than from a game's seed, since a code is
    a capability and a seeded table is meant to deal the same cards twice.
    """
    return written(tuple(choice(RANK_SEQUENCE) for _ in range(CODE_LENGTH)))


def written(ranks: Ranks) -> str:
    """A hand of ranks as a code is written down, which is the form an address carries."""
    return "".join(ranks)


def spoken(ranks: Ranks) -> str:
    """A hand of ranks as a code is read out, one rank apart from the next."""
    return APART.join(ranks)


def ranks_in(offered: str) -> Ranks | None:
    """The hand of ranks a code reads as, and None where what was offered reads as no hand at all.

    Reading runs left to right over the code in capitals with the spaces and dashes a person writes it with
    dropped, and takes the longest rank standing at each place, so `10` is read where `1` would be. Neither
    `1` nor `0` names a rank on its own, which leaves one reading for every code: `K10AJ2` reads as five ranks
    and `012345` as none.
    """
    tidy = _tidied(offered)
    if not tidy:
        return None

    read: list[Rank] = []
    place = 0
    while place < len(tidy):
        rank = _rank_at(tidy, place)
        if rank is None:
            return None

        read.append(rank)
        place += len(rank.value)

    return tuple(read)


def admits(code: str, offered: str) -> bool:
    """Whether what someone offered reads as the same hand of ranks a code is.

    Both are read into ranks first, so a code admits however it was written down — spaced, hyphenated or in
    lower case — and the two hands are then compared under `compare_digest`, which takes the same time
    whatever they hold and so tells a wrong code nothing about how much of it was right.
    """
    held = ranks_in(code)
    read = ranks_in(offered)
    if held is None or read is None:
        return False

    return compare_digest(written(held), written(read))


def _tidied(offered: str) -> str:
    """A code as it comes to be read: in capitals, with the separators a person writes it with dropped."""
    return "".join(character for character in offered.upper() if character not in SEPARATORS)


def _rank_at(tidy: str, place: int) -> Rank | None:
    """The rank standing at one place of a tidied code, which is the longest one reading there."""
    for length in range(LONGEST_RANK, 0, -1):
        rank = READ_AS.get(tidy[place : place + length])
        if rank is not None:
            return rank

    return None
