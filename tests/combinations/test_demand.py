from dataclasses import dataclass
from typing import Final

import pytest

from cardwork.cards.card import Card
from cardwork.cards.cards import (
    ACE_OF_SPADES,
    KING_OF_HEARTS,
    KING_OF_SPADES,
    STANDARD_CARDS,
)
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.combinations.demand import ANY_CARD, Demand
from cardwork.combinations.policy import REGULAR_EVALUATION
from tests.cases import Case, descriptions

KING_OF_SPADES_DEMAND: Final[Demand] = Demand(rank=Rank.KING, suit=Suit.SPADE)


@dataclass(frozen=True)
class AdmitsCase(Case):
    demand: Demand
    card: Card
    admits: bool


ADMITS: Final[tuple[AdmitsCase, ...]] = (
    AdmitsCase(
        description="a rank admits any card of it",
        demand=Demand.of_rank(Rank.KING),
        card=KING_OF_HEARTS,
        admits=True,
    ),
    AdmitsCase(
        description="a rank turns another rank away",
        demand=Demand.of_rank(Rank.KING),
        card=ACE_OF_SPADES,
        admits=False,
    ),
    AdmitsCase(
        description="a suit admits any card of it",
        demand=Demand.of_suit(Suit.SPADE),
        card=ACE_OF_SPADES,
        admits=True,
    ),
    AdmitsCase(
        description="a suit turns another suit away",
        demand=Demand.of_suit(Suit.SPADE),
        card=KING_OF_HEARTS,
        admits=False,
    ),
    AdmitsCase(
        description="a rank and a suit admit the one card holding both",
        demand=KING_OF_SPADES_DEMAND,
        card=KING_OF_SPADES,
        admits=True,
    ),
    AdmitsCase(
        description="a rank and a suit turn away a card holding one of them",
        demand=KING_OF_SPADES_DEMAND,
        card=KING_OF_HEARTS,
        admits=False,
    ),
    AdmitsCase(
        description="a loose place admits whatever comes",
        demand=ANY_CARD,
        card=KING_OF_HEARTS,
        admits=True,
    ),
)


@pytest.mark.parametrize("case", ADMITS, ids=descriptions(ADMITS))
def test_a_demand_states_the_cards_it_admits(case: AdmitsCase) -> None:
    assert case.demand.admits(case.card) is case.admits


@dataclass(frozen=True)
class MeetCase(Case):
    left: Demand
    right: Demand
    met: Demand | None


MEETS: Final[tuple[MeetCase, ...]] = (
    MeetCase(
        description="a rank and a suit ask for the one card holding both",
        left=Demand.of_rank(Rank.KING),
        right=Demand.of_suit(Suit.SPADE),
        met=KING_OF_SPADES_DEMAND,
    ),
    MeetCase(
        description="a loose place takes whatever the other asks",
        left=ANY_CARD,
        right=Demand.of_rank(Rank.KING),
        met=Demand.of_rank(Rank.KING),
    ),
    MeetCase(
        description="two loose places stay loose",
        left=ANY_CARD,
        right=ANY_CARD,
        met=ANY_CARD,
    ),
    MeetCase(
        description="one rank asked twice stands as it is",
        left=Demand.of_rank(Rank.KING),
        right=Demand.of_rank(Rank.KING),
        met=Demand.of_rank(Rank.KING),
    ),
    MeetCase(
        description="two ranks at one place leave it asking the impossible",
        left=Demand.of_rank(Rank.KING),
        right=Demand.of_rank(Rank.ACE),
        met=None,
    ),
    MeetCase(
        description="two suits at one place leave it asking the impossible likewise",
        left=Demand.of_suit(Suit.SPADE),
        right=Demand.of_suit(Suit.HEART),
        met=None,
    ),
    MeetCase(
        description="a card and another suit of its rank ask the impossible",
        left=KING_OF_SPADES_DEMAND,
        right=Demand.of_suit(Suit.HEART),
        met=None,
    ),
)


@pytest.mark.parametrize("case", MEETS, ids=descriptions(MEETS))
def test_two_demands_on_one_place_ask_what_both_ask(case: MeetCase) -> None:
    assert case.left.meet(case.right) == case.met
    assert case.right.meet(case.left) == case.met


@dataclass(frozen=True)
class CandidatesCase(Case):
    demand: Demand
    candidates: int
    strongest: Card


CANDIDATES: Final[tuple[CandidatesCase, ...]] = (
    CandidatesCase(
        description="a rank is held by one card per suit",
        demand=Demand.of_rank(Rank.KING),
        candidates=len(Suit),
        strongest=KING_OF_SPADES,
    ),
    CandidatesCase(
        description="a suit is held by one card per rank",
        demand=Demand.of_suit(Suit.SPADE),
        candidates=len(Rank),
        strongest=ACE_OF_SPADES,
    ),
    CandidatesCase(
        description="a card is held by itself alone",
        demand=KING_OF_SPADES_DEMAND,
        candidates=1,
        strongest=KING_OF_SPADES,
    ),
    CandidatesCase(
        description="a loose place is held by the whole deck",
        demand=ANY_CARD,
        candidates=len(STANDARD_CARDS),
        strongest=ACE_OF_SPADES,
    ),
)


@pytest.mark.parametrize("case", CANDIDATES, ids=descriptions(CANDIDATES))
def test_a_demand_names_every_card_it_admits_from_the_strongest_down(case: CandidatesCase) -> None:
    candidates = case.demand.candidates(REGULAR_EVALUATION)
    order = REGULAR_EVALUATION.card_order()

    assert len(candidates) == case.candidates
    assert candidates[0] == case.strongest
    assert candidates == order.descending(candidates)
    assert all(case.demand.admits(card) for card in candidates)
