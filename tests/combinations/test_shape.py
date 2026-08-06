from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.combinations.demand import ANY_CARD, Demand
from cardwork.combinations.shape import Shape
from tests.cases import Case, descriptions

TWO_KINGS: Final[Shape] = Shape(demands=(Demand.of_rank(Rank.KING),) * 2, low_ace=False)
TWO_QUEENS: Final[Shape] = Shape(demands=(Demand.of_rank(Rank.QUEEN),) * 2, low_ace=False)
TWO_SPADES: Final[Shape] = Shape(demands=(Demand.of_suit(Suit.SPADE),) * 2, low_ace=False)
TWO_HEARTS: Final[Shape] = Shape(demands=(Demand.of_suit(Suit.HEART),) * 2, low_ace=False)
TWO_LOOSE: Final[Shape] = Shape(demands=(ANY_CARD,) * 2, low_ace=False)
ACE_AND_TWO: Final[Shape] = Shape(demands=(Demand.of_rank(Rank.ACE), Demand.of_rank(Rank.TWO)), low_ace=True)


def test_a_shape_reads_the_places_it_holds() -> None:
    assert TWO_KINGS.size == 2
    assert TWO_KINGS.ranks == frozenset({Rank.KING})
    assert TWO_KINGS.suits == frozenset()
    assert TWO_SPADES.suits == frozenset({Suit.SPADE})
    assert TWO_LOOSE.ranks == frozenset()
    assert ACE_AND_TWO.ranks == frozenset({Rank.ACE, Rank.TWO})


@dataclass(frozen=True)
class TogetherCase(Case):
    shapes: tuple[Shape, ...]
    met: Shape | None


TOGETHERS: Final[tuple[TogetherCase, ...]] = (
    TogetherCase(
        description="a run read with a suit asks each place for one card",
        shapes=(ACE_AND_TWO, TWO_SPADES),
        met=Shape(
            demands=(Demand(rank=Rank.ACE, suit=Suit.SPADE), Demand(rank=Rank.TWO, suit=Suit.SPADE)),
            low_ace=True,
        ),
    ),
    TogetherCase(
        description="a loose reading takes whatever it is read with",
        shapes=(TWO_LOOSE, TWO_KINGS),
        met=TWO_KINGS,
    ),
    TogetherCase(
        description="two suits at one place leave the reading impossible",
        shapes=(TWO_SPADES, TWO_HEARTS),
        met=None,
    ),
    TogetherCase(
        description="two ranks at one place leave the reading impossible likewise",
        shapes=(TWO_KINGS, TWO_QUEENS),
        met=None,
    ),
    TogetherCase(
        description="three readings meet at once",
        shapes=(TWO_LOOSE, TWO_KINGS, TWO_SPADES),
        met=Shape(demands=(Demand(rank=Rank.KING, suit=Suit.SPADE),) * 2, low_ace=False),
    ),
)


@pytest.mark.parametrize("case", TOGETHERS, ids=descriptions(TOGETHERS))
def test_readings_taken_together_ask_what_all_of_them_ask(case: TogetherCase) -> None:
    assert Shape.together(case.shapes) == case.met


def test_readings_standing_beside_each_other_hold_every_place_of_both() -> None:
    joined = Shape.beside((TWO_KINGS, ACE_AND_TWO))

    assert joined.demands == (*TWO_KINGS.demands, *ACE_AND_TWO.demands)
    assert joined.size == 4
    assert joined.low_ace is True
    assert Shape.beside((TWO_KINGS, TWO_QUEENS)).low_ace is False


@dataclass(frozen=True)
class ApartCase(Case):
    shapes: tuple[Shape, ...]
    apart: bool


APARTS: Final[tuple[ApartCase, ...]] = (
    ApartCase(
        description="two ranks keep places of their own",
        shapes=(TWO_KINGS, TWO_QUEENS),
        apart=True,
    ),
    ApartCase(
        description="one rank named twice is one rank",
        shapes=(TWO_KINGS, TWO_KINGS),
        apart=False,
    ),
    ApartCase(
        description="two suits keep places of their own",
        shapes=(TWO_SPADES, TWO_HEARTS),
        apart=True,
    ),
    ApartCase(
        description="one suit named twice is one suit",
        shapes=(TWO_SPADES, TWO_SPADES),
        apart=False,
    ),
    ApartCase(
        description="a rank and a suit name nothing in common",
        shapes=(TWO_KINGS, TWO_SPADES),
        apart=True,
    ),
    ApartCase(
        description="a loose reading names nothing, so it stands beside anything",
        shapes=(TWO_LOOSE, TWO_LOOSE),
        apart=True,
    ),
    ApartCase(
        description="three readings hold apart only where each is apart from both others",
        shapes=(TWO_KINGS, TWO_QUEENS, ACE_AND_TWO),
        apart=True,
    ),
    ApartCase(
        description="a rank shared with a third reading holds them together",
        shapes=(TWO_KINGS, TWO_QUEENS, TWO_KINGS),
        apart=False,
    ),
)


@pytest.mark.parametrize("case", APARTS, ids=descriptions(APARTS))
def test_readings_stand_apart_where_each_names_ranks_and_suits_of_its_own(case: ApartCase) -> None:
    assert Shape.apart(case.shapes) is case.apart
