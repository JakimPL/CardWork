from dataclasses import dataclass
from itertools import combinations
from typing import Final

import pytest

from cardgames.backend.shedding.rules import (
    HAND_SIZE,
    NOTHING,
    ROUND_POINT,
    drawn_from,
    gone_out,
    holds_a_set,
    may_act,
    ranked,
    reads_alike,
    sets_in,
    taken_by,
)
from cardwork.cards.cards import (
    FIVE_OF_CLUBS,
    FIVE_OF_DIAMONDS,
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    KING_OF_CLUBS,
    NINE_OF_CLUBS,
    NINE_OF_DIAMONDS,
    RED_JOKER,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardsOrJokers
from cardwork.cards.rank import Rank
from cardwork.decks.deck import Indices
from cardwork.exceptions import LogicError
from tests.cases import Case, descriptions

FULL_STOCK: Final[int] = 40
RUN_OUT: Final[int] = 0
A_PAIR: Final[CardsOrJokers] = (FIVE_OF_SPADES, FIVE_OF_HEARTS)
ODD_CARDS: Final[CardsOrJokers] = (TWO_OF_SPADES, NINE_OF_DIAMONDS)
A_LONG_HAND: Final[CardsOrJokers] = (
    FIVE_OF_SPADES,
    FIVE_OF_HEARTS,
    FIVE_OF_DIAMONDS,
    NINE_OF_DIAMONDS,
    NINE_OF_CLUBS,
)


def named(*sets: tuple[int, ...]) -> frozenset[Indices]:
    """The sets a hand is expected to offer, each named by the positions it holds."""
    return frozenset(frozenset(places) for places in sets)


@dataclass(frozen=True)
class SetCase(Case):
    """One hand and the whole of what the rules read in it: the sets it offers, and whether it is one itself."""

    hand: CardsOrJokers
    alike: bool
    holds: bool
    sets: frozenset[Indices]


CASES: Final[tuple[SetCase, ...]] = (
    SetCase(
        description="a pair standing alone is the one set it offers",
        hand=A_PAIR,
        alike=True,
        holds=True,
        sets=named((0, 1)),
    ),
    SetCase(
        description="a pair beside an odd card offers the pair",
        hand=(FIVE_OF_SPADES, FIVE_OF_HEARTS, NINE_OF_DIAMONDS),
        alike=False,
        holds=True,
        sets=named((0, 1)),
    ),
    SetCase(
        description="three of a rank offer both of their pairs beside the three of them",
        hand=(FIVE_OF_SPADES, FIVE_OF_HEARTS, FIVE_OF_DIAMONDS),
        alike=True,
        holds=True,
        sets=named((0, 1), (0, 2), (1, 2), (0, 1, 2)),
    ),
    SetCase(
        description="four of a rank offer every pair and every three of them beside the four",
        hand=(FIVE_OF_SPADES, FIVE_OF_HEARTS, FIVE_OF_DIAMONDS, FIVE_OF_CLUBS),
        alike=True,
        holds=True,
        sets=named(
            (0, 1),
            (0, 2),
            (0, 3),
            (1, 2),
            (1, 3),
            (2, 3),
            (0, 1, 2),
            (0, 1, 3),
            (0, 2, 3),
            (1, 2, 3),
            (0, 1, 2, 3),
        ),
    ),
    SetCase(
        description="two pairs offer one set apiece and none across the two ranks",
        hand=(FIVE_OF_SPADES, FIVE_OF_HEARTS, NINE_OF_DIAMONDS, NINE_OF_CLUBS),
        alike=False,
        holds=True,
        sets=named((0, 1), (2, 3)),
    ),
    SetCase(
        description="a hand of cards sharing no rank offers nothing",
        hand=(TWO_OF_SPADES, FIVE_OF_HEARTS, NINE_OF_DIAMONDS, KING_OF_CLUBS),
        alike=False,
        holds=False,
        sets=named(),
    ),
    SetCase(
        description="one card falls short of the two a set is read from",
        hand=(TWO_OF_SPADES,),
        alike=False,
        holds=False,
        sets=named(),
    ),
    SetCase(
        description="a hand holding nothing offers nothing",
        hand=(),
        alike=False,
        holds=False,
        sets=named(),
    ),
)


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
def test_a_hand_offers_the_sets_its_repeated_ranks_hold(case: SetCase) -> None:
    offered = sets_in(case.hand)

    assert reads_alike(case.hand) is case.alike
    assert holds_a_set(case.hand) is case.holds
    assert frozenset(offered) == case.sets
    assert len(offered) == len(case.sets)


@pytest.mark.parametrize("case", CASES, ids=descriptions(CASES))
def test_every_set_a_hand_offers_is_read_as_one_rank(case: SetCase) -> None:
    """The two readings of one rule: the sets a hand lists, and the set a client's own selection is held to."""
    for places in sets_in(case.hand):
        assert reads_alike(tuple(case.hand[place] for place in sorted(places)))


def test_the_sets_a_hand_offers_are_every_selection_the_rules_would_admit() -> None:
    """Nothing a client could select reads as one rank without standing on the list the rules enumerate."""
    places = range(len(A_LONG_HAND))
    admitted = {
        frozenset(chosen)
        for size in places
        for chosen in combinations(places, size + 1)
        if reads_alike(tuple(A_LONG_HAND[place] for place in chosen))
    }

    assert frozenset(sets_in(A_LONG_HAND)) == admitted


def test_a_card_reads_as_the_rank_it_carries() -> None:
    assert ranked(FIVE_OF_SPADES) == Rank.FIVE


def test_a_joker_reads_as_no_rank_this_game_is_played_with() -> None:
    with pytest.raises(LogicError, match="suited cards alone"):
        ranked(RED_JOKER)


def test_a_draw_takes_the_card_at_the_end_of_the_stock() -> None:
    assert drawn_from(FULL_STOCK) == frozenset({FULL_STOCK - 1})
    assert drawn_from(1) == frozenset({RUN_OUT})


def test_a_draw_from_a_stock_that_has_run_out_is_refused() -> None:
    with pytest.raises(LogicError, match="has run out"):
        drawn_from(RUN_OUT)


def test_a_seat_has_a_turn_to_take_while_it_holds_a_set_or_the_stock_holds_a_card() -> None:
    assert may_act(A_PAIR, FULL_STOCK) is True
    assert may_act(A_PAIR, RUN_OUT) is True
    assert may_act(ODD_CARDS, FULL_STOCK) is True
    assert may_act(ODD_CARDS, RUN_OUT) is False


def test_the_round_goes_to_the_shortest_hand_at_the_table() -> None:
    assert taken_by((HAND_SIZE, 1, 3)) == (NOTHING, ROUND_POINT, NOTHING)


def test_a_round_two_seats_stand_equally_short_in_goes_to_each_of_them() -> None:
    assert taken_by((1, HAND_SIZE, 1)) == (ROUND_POINT, NOTHING, ROUND_POINT)


def test_a_seat_that_shed_its_last_card_went_out() -> None:
    assert gone_out((3, RUN_OUT, 1)) == 1


def test_a_round_every_seat_is_still_holding_a_card_in_left_nobody_out() -> None:
    assert gone_out((3, 1, 1)) is None
