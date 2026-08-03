from collections.abc import Sequence
from dataclasses import dataclass
from itertools import permutations, product
from typing import Final

import pytest
from hypothesis import given
from hypothesis import strategies as st

from cardwork.combinations.matching import UNPLACED, Matching

from ..cases import Case, descriptions

MOST_OFFERS: Final[int] = 4
MOST_PLACES: Final[int] = 4

type Graph = tuple[tuple[tuple[int, ...], ...], int]


@dataclass(frozen=True)
class PlacedCase(Case):
    admitted: tuple[tuple[int, ...], ...]
    places: int
    taken: tuple[int, ...]


PLACINGS: Final[tuple[PlacedCase, ...]] = (
    PlacedCase(
        description="one offer takes the place it answers",
        admitted=((0,),),
        places=1,
        taken=(0,),
    ),
    PlacedCase(
        description="offers standing open take a place each",
        admitted=((0, 1), (0, 1)),
        places=2,
        taken=(0, 1),
    ),
    PlacedCase(
        description="an offer answering no place stands out of the way",
        admitted=((), (0,)),
        places=1,
        taken=(UNPLACED, 0),
    ),
    PlacedCase(
        description="two offers on one place leave the later of them unplaced",
        admitted=((0,), (0,)),
        places=1,
        taken=(0, UNPLACED),
    ),
    PlacedCase(
        description="a holder moves on where another offer answers its place alone",
        admitted=((0, 1), (0,)),
        places=2,
        taken=(1, 0),
    ),
    PlacedCase(
        description="a chain of holders moves on together",
        admitted=((0, 1, 2), (0, 1), (0,)),
        places=3,
        taken=(2, 1, 0),
    ),
    PlacedCase(
        description="a pair of kings beside three spades rearranges to hold both",
        admitted=((0, 1, 2, 3, 4), (0, 1), (0, 1), (2, 3, 4), (2, 3, 4)),
        places=5,
        taken=(2, 1, 0, 3, 4),
    ),
    PlacedCase(
        description="one place among three offers holds the first of them",
        admitted=((0,), (0,), (0,)),
        places=1,
        taken=(0, UNPLACED, UNPLACED),
    ),
    PlacedCase(
        description="no places leave every offer unplaced",
        admitted=((), ()),
        places=0,
        taken=(UNPLACED, UNPLACED),
    ),
    PlacedCase(
        description="no offers fill no places",
        admitted=(),
        places=3,
        taken=(),
    ),
)


@pytest.mark.parametrize("case", PLACINGS, ids=descriptions(PLACINGS))
def test_offers_take_the_places_they_answer(case: PlacedCase) -> None:
    assert Matching(case.admitted, case.places).placements == case.taken


@st.composite
def _graphs(draw: st.DrawFn) -> Graph:
    places = draw(st.integers(min_value=0, max_value=MOST_PLACES))
    offers = draw(st.integers(min_value=0, max_value=MOST_OFFERS))
    if places == 0:
        return tuple(() for _ in range(offers)), places

    answered = st.sets(st.integers(min_value=0, max_value=places - 1), max_size=places)
    return tuple(tuple(sorted(draw(answered))) for _ in range(offers)), places


def _sound(admitted: Sequence[Sequence[int]], choice: Sequence[int]) -> bool:
    """Whether this assignment gives every placed offer a place of its own that it answers."""
    held = [place for place in choice if place != UNPLACED]
    return len(set(held)) == len(held) and all(
        place in admitted[offer] for offer, place in enumerate(choice) if place != UNPLACED
    )


def _largest(admitted: Sequence[Sequence[int]], places: int) -> int:
    """The most offers any assignment places, found by trying every assignment there is."""
    return max(
        sum(1 for place in choice if place != UNPLACED)
        for choice in product((UNPLACED, *range(places)), repeat=len(admitted))
        if _sound(admitted, choice)
    )


def _fits(admitted: Sequence[Sequence[int]], places: int, offers: Sequence[int]) -> bool:
    """Whether these offers hold places of their own all at once."""
    return any(
        all(place in admitted[offer] for offer, place in zip(offers, choice, strict=True))
        for choice in permutations(range(places), len(offers))
    )


@given(graph=_graphs())
def test_as_many_offers_are_placed_as_any_assignment_could_place(graph: Graph) -> None:
    admitted, places = graph

    taken = Matching(admitted, places).placements

    assert _sound(admitted, taken)
    assert sum(1 for place in taken if place != UNPLACED) == _largest(admitted, places)


@given(graph=_graphs())
def test_the_offers_standing_earliest_are_the_ones_placed(graph: Graph) -> None:
    admitted, places = graph

    taken = Matching(admitted, places).placements

    for offer, place in enumerate(taken):
        if place == UNPLACED:
            standing = [before for before, held in enumerate(taken[:offer]) if held != UNPLACED]
            assert not _fits(admitted, places, (*standing, offer))
