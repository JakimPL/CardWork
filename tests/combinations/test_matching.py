from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from itertools import product
from typing import Final

import pytest
from hypothesis import given
from hypothesis import strategies as st

from cardwork.combinations.matching import UNPLACED, Matching, Seat
from tests.cases import Case, descriptions

MOST_OFFERS: Final[int] = 4
MOST_PLACES: Final[int] = 4
MOST_GATES: Final[int] = 3
UNSEATED: Final[int] = -1

type Seats = tuple[tuple[Seat, ...], ...]


@dataclass(frozen=True)
class Seating(Case):
    """One run of offers beside the seats each answers, which one gate to a place is what a shape states."""

    seats: Seats
    places: int
    gates: int


@dataclass(frozen=True)
class PlacedCase(Seating):
    taken: tuple[int, ...]


def _ungated(admitted: tuple[tuple[int, ...], ...]) -> Seats:
    """Those places as seats, each place passing a gate of its own, which a shape holding none apart states."""
    return tuple(tuple((place, place) for place in answered) for answered in admitted)


PLACINGS: Final[tuple[PlacedCase, ...]] = (
    PlacedCase(
        description="one offer takes the place it answers",
        seats=_ungated(((0,),)),
        places=1,
        gates=1,
        taken=(0,),
    ),
    PlacedCase(
        description="offers standing open take a place each",
        seats=_ungated(((0, 1), (0, 1))),
        places=2,
        gates=2,
        taken=(0, 1),
    ),
    PlacedCase(
        description="an offer answering no place stands out of the way",
        seats=_ungated(((), (0,))),
        places=1,
        gates=1,
        taken=(UNPLACED, 0),
    ),
    PlacedCase(
        description="two offers on one place leave the later of them unplaced",
        seats=_ungated(((0,), (0,))),
        places=1,
        gates=1,
        taken=(0, UNPLACED),
    ),
    PlacedCase(
        description="a holder moves on where another offer answers its place alone",
        seats=_ungated(((0, 1), (0,))),
        places=2,
        gates=2,
        taken=(1, 0),
    ),
    PlacedCase(
        description="a chain of holders moves on together",
        seats=_ungated(((0, 1, 2), (0, 1), (0,))),
        places=3,
        gates=3,
        taken=(2, 1, 0),
    ),
    PlacedCase(
        description="a pair of kings beside three spades rearranges to hold both",
        seats=_ungated(((0, 1, 2, 3, 4), (0, 1), (0, 1), (2, 3, 4), (2, 3, 4))),
        places=5,
        gates=5,
        taken=(2, 1, 0, 3, 4),
    ),
    PlacedCase(
        description="one place among three offers holds the first of them",
        seats=_ungated(((0,), (0,), (0,))),
        places=1,
        gates=1,
        taken=(0, UNPLACED, UNPLACED),
    ),
    PlacedCase(
        description="no places leave every offer unplaced",
        seats=_ungated(((), ())),
        places=0,
        gates=0,
        taken=(UNPLACED, UNPLACED),
    ),
    PlacedCase(
        description="no offers fill no places",
        seats=(),
        places=3,
        gates=3,
        taken=(),
    ),
    PlacedCase(
        description="two offers passing one gate fill one place between them",
        seats=(((0, 0), (1, 0)), ((0, 0), (1, 0))),
        places=2,
        gates=1,
        taken=(0, UNPLACED),
    ),
    PlacedCase(
        description="offers passing gates of their own fill a place each",
        seats=(((0, 0), (1, 0)), ((0, 1), (1, 1))),
        places=2,
        gates=2,
        taken=(0, 1),
    ),
    PlacedCase(
        description="an offer keeps the gate it passes and moves to a place behind it",
        seats=(((0, 0), (1, 0)), ((0, 1),)),
        places=2,
        gates=2,
        taken=(1, 0),
    ),
    PlacedCase(
        description="a holder keeps its gate and moves aside for an offer passing another",
        seats=(((0, 0), (1, 0)), ((0, 0), (1, 0)), ((0, 1),)),
        places=2,
        gates=2,
        taken=(1, UNPLACED, 0),
    ),
)


@pytest.mark.parametrize("case", PLACINGS, ids=descriptions(PLACINGS))
def test_offers_take_the_seats_they_answer(case: PlacedCase) -> None:
    assert Matching(case.seats, case.places, case.gates).placements == case.taken


@st.composite
def _seatings(draw: st.DrawFn) -> Seating:
    """A seating in the shape `Seating` states them.

    Every place stands behind one gate, as a place reads apart in one spread at the most, and the offers
    reaching a gate reach the same places through it, as the cards showing one facing do where the places of a
    spread ask alike. An offer answers the places behind the gates it passes.
    """
    places = draw(st.integers(min_value=0, max_value=MOST_PLACES))
    gates = draw(st.integers(min_value=1, max_value=MOST_GATES))
    kept = [draw(st.integers(min_value=0, max_value=gates - 1)) for _ in range(places)]
    behind = [tuple(place for place, gate in enumerate(kept) if gate == passing) for passing in range(gates)]
    offers = draw(st.integers(min_value=0, max_value=MOST_OFFERS))
    seats: list[tuple[Seat, ...]] = []
    for _ in range(offers):
        passing = draw(st.sets(st.integers(min_value=0, max_value=gates - 1), max_size=gates))
        seats.append(tuple((place, gate) for gate in sorted(passing) for place in behind[gate]))

    return Seating(description="a drawn seating", seats=tuple(seats), places=places, gates=gates)


def _sound(seating: Seating, choice: Sequence[int]) -> bool:
    """Whether this assignment gives every placed offer a place and a gate of its own that it answers."""
    seats = [seating.seats[offer][pick] for offer, pick in enumerate(choice) if pick != UNSEATED]
    places = [place for place, _ in seats]
    gates = [gate for _, gate in seats]
    return len(set(places)) == len(places) and len(set(gates)) == len(gates)


def _choices(seating: Seating) -> Iterator[tuple[int, ...]]:
    """Every way of seating the offers, an offer left out of the seating included."""
    return product(*((UNSEATED, *range(len(answered))) for answered in seating.seats))


def _largest(seating: Seating) -> int:
    """The most offers any seating places, found by trying every seating there is."""
    return max(sum(1 for pick in choice if pick != UNSEATED) for choice in _choices(seating) if _sound(seating, choice))


def _fits(seating: Seating, offers: Sequence[int]) -> bool:
    """Whether these offers hold seats of their own all at once."""
    standing = tuple(offers)
    return any(
        _sound(seating, choice)
        for choice in _choices(seating)
        if all((pick != UNSEATED) is (offer in standing) for offer, pick in enumerate(choice))
    )


@given(seating=_seatings())
def test_as_many_offers_are_placed_as_any_seating_could_place(seating: Seating) -> None:
    taken = Matching(seating.seats, seating.places, seating.gates).placements

    assert _sound(seating, _picked(seating, taken))
    assert sum(1 for place in taken if place != UNPLACED) == _largest(seating)


@given(seating=_seatings())
def test_the_offers_standing_earliest_are_the_ones_placed(seating: Seating) -> None:
    taken = Matching(seating.seats, seating.places, seating.gates).placements

    for offer, place in enumerate(taken):
        if place == UNPLACED:
            standing = [before for before, held in enumerate(taken[:offer]) if held != UNPLACED]
            assert not _fits(seating, (*standing, offer))


def _picked(seating: Seating, taken: Sequence[int]) -> tuple[int, ...]:
    """The seat each offer took, named by where it stands in the seats that offer answers."""
    return tuple(
        (
            next(
                (pick for pick, (place, _) in enumerate(seating.seats[offer]) if place == held),
                UNSEATED,
            )
            if held != UNPLACED
            else UNSEATED
        )
        for offer, held in enumerate(taken)
    )
