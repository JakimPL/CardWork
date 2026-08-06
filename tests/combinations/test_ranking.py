from dataclasses import dataclass
from itertools import combinations
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.cards.card import Card
from cardwork.cards.cards import (
    ACE_OF_CLUBS,
    ACE_OF_HEARTS,
    ACE_OF_SPADES,
    FIVE_OF_DIAMONDS,
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    FOUR_OF_CLUBS,
    FOUR_OF_SPADES,
    JACK_OF_HEARTS,
    JACK_OF_SPADES,
    KING_OF_CLUBS,
    KING_OF_DIAMONDS,
    KING_OF_HEARTS,
    KING_OF_SPADES,
    NINE_OF_SPADES,
    QUEEN_OF_DIAMONDS,
    QUEEN_OF_HEARTS,
    QUEEN_OF_SPADES,
    SEVEN_OF_DIAMONDS,
    SEVEN_OF_HEARTS,
    SEVEN_OF_SPADES,
    SIX_OF_SPADES,
    STANDARD_CARDS,
    TEN_OF_SPADES,
    THREE_OF_CLUBS,
    THREE_OF_HEARTS,
    THREE_OF_SPADES,
    TWO_OF_CLUBS,
    TWO_OF_HEARTS,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardOrJoker
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.combinations.detect import find
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.patterns.same_rank import SameRank
from cardwork.combinations.patterns.same_suit import SameSuit
from cardwork.combinations.poker import (
    APART_FULL_HOUSE,
    APART_PAIR,
    APART_POKER,
    APART_POKER_ORDER,
    APART_QUADRUPLET,
    APART_TWO_PAIR,
    FLUSH,
    FULL_HOUSE,
    HIGH_CARD,
    PAIR,
    POKER,
    POKER_HAND,
    POKER_ORDER,
    QUADRUPLET,
    STRAIGHT,
    STRAIGHT_FLUSH,
    TRIPLET,
    TWO_PAIR,
)
from cardwork.combinations.policy import REGULAR_EVALUATION
from cardwork.combinations.ranking import Ranking

THREE_OF_A_SUIT: Final[Pattern] = SameSuit(places=3)
FIVE_OF_A_RANK: Final[Pattern] = SameRank(places=POKER_HAND)
ALIKE_ALONE: Final[Ranking] = Ranking(patterns=(HIGH_CARD, PAIR, TRIPLET), evaluation=REGULAR_EVALUATION)
FIVES_APART: Final[Ranking] = Ranking(patterns=(PAIR, FIVE_OF_A_RANK), evaluation=REGULAR_EVALUATION)

SINGLE_CARD: Final[int] = 1
PAIR_CARDS: Final[int] = 2
TRIPLET_CARDS: Final[int] = 3
TWO_PAIR_CARDS: Final[int] = 4
PAST_THE_RANKING: Final[int] = 6

from tests.cases import Case, descriptions

ROYAL_FLUSH: Final[tuple[CardOrJoker, ...]] = (
    TEN_OF_SPADES,
    JACK_OF_SPADES,
    QUEEN_OF_SPADES,
    KING_OF_SPADES,
    ACE_OF_SPADES,
)
FOUR_KINGS: Final[tuple[CardOrJoker, ...]] = (
    KING_OF_SPADES,
    KING_OF_HEARTS,
    KING_OF_CLUBS,
    KING_OF_DIAMONDS,
    TWO_OF_SPADES,
)
KINGS_OVER_FIVES: Final[tuple[CardOrJoker, ...]] = (
    KING_OF_SPADES,
    KING_OF_HEARTS,
    KING_OF_CLUBS,
    FIVE_OF_SPADES,
    FIVE_OF_HEARTS,
)
SPADE_FLUSH: Final[tuple[CardOrJoker, ...]] = (
    ACE_OF_SPADES,
    NINE_OF_SPADES,
    FIVE_OF_SPADES,
    THREE_OF_SPADES,
    TWO_OF_SPADES,
)
SIX_HIGH_STRAIGHT: Final[tuple[CardOrJoker, ...]] = (
    TWO_OF_SPADES,
    THREE_OF_HEARTS,
    FOUR_OF_CLUBS,
    FIVE_OF_DIAMONDS,
    SIX_OF_SPADES,
)
WHEEL: Final[tuple[CardOrJoker, ...]] = (
    ACE_OF_SPADES,
    TWO_OF_HEARTS,
    THREE_OF_CLUBS,
    FOUR_OF_CLUBS,
    FIVE_OF_SPADES,
)
KINGS: Final[tuple[CardOrJoker, ...]] = (KING_OF_SPADES, KING_OF_HEARTS, TWO_OF_CLUBS)
OTHER_KINGS: Final[tuple[CardOrJoker, ...]] = (KING_OF_DIAMONDS, KING_OF_CLUBS, THREE_OF_CLUBS)
FIVES: Final[tuple[CardOrJoker, ...]] = (FIVE_OF_SPADES, FIVE_OF_HEARTS, TWO_OF_CLUBS)
THREE_KINGS: Final[tuple[CardOrJoker, ...]] = (KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS)
FOUR_KINGS_ALONE: Final[tuple[CardOrJoker, ...]] = (
    KING_OF_SPADES,
    KING_OF_HEARTS,
    KING_OF_CLUBS,
    KING_OF_DIAMONDS,
)
KING_HELD_TWICE: Final[tuple[CardOrJoker, ...]] = (KING_OF_SPADES, KING_OF_SPADES)
TRIPLET_LEANING: Final[tuple[CardOrJoker, ...]] = (KING_OF_SPADES, KING_OF_SPADES, KING_OF_HEARTS)
TWO_PAIR_OF_TWO_SUITS: Final[tuple[CardOrJoker, ...]] = (
    KING_OF_SPADES,
    KING_OF_HEARTS,
    QUEEN_OF_SPADES,
    QUEEN_OF_HEARTS,
)
TWO_PAIR_LEANING: Final[tuple[CardOrJoker, ...]] = (
    KING_OF_SPADES,
    KING_OF_SPADES,
    QUEEN_OF_SPADES,
    QUEEN_OF_HEARTS,
)
FULL_HOUSE_LEANING: Final[tuple[CardOrJoker, ...]] = (
    KING_OF_SPADES,
    KING_OF_SPADES,
    KING_OF_HEARTS,
    QUEEN_OF_SPADES,
    QUEEN_OF_HEARTS,
)
FLUSH_LEANING: Final[tuple[CardOrJoker, ...]] = (
    TWO_OF_SPADES,
    TWO_OF_SPADES,
    THREE_OF_SPADES,
    FOUR_OF_SPADES,
    FIVE_OF_SPADES,
)
QUEENS_OVER_JACKS: Final[tuple[CardOrJoker, ...]] = (
    QUEEN_OF_SPADES,
    QUEEN_OF_HEARTS,
    QUEEN_OF_DIAMONDS,
    JACK_OF_SPADES,
    JACK_OF_HEARTS,
)


@dataclass(frozen=True)
class StrongestCase(Case):
    cards: tuple[CardOrJoker, ...]
    pattern: Pattern | None
    reading: tuple[Card, ...] | None


STRONGEST: Final[tuple[StrongestCase, ...]] = (
    StrongestCase(
        description="five spades in a row are a straight flush",
        cards=ROYAL_FLUSH,
        pattern=STRAIGHT_FLUSH,
        reading=(TEN_OF_SPADES, JACK_OF_SPADES, QUEEN_OF_SPADES, KING_OF_SPADES, ACE_OF_SPADES),
    ),
    StrongestCase(
        description="four kings are a quadruplet",
        cards=FOUR_KINGS,
        pattern=QUADRUPLET,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_DIAMONDS, KING_OF_CLUBS),
    ),
    StrongestCase(
        description="three kings and two fives are a full house",
        cards=KINGS_OVER_FIVES,
        pattern=FULL_HOUSE,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS, FIVE_OF_SPADES, FIVE_OF_HEARTS),
    ),
    StrongestCase(
        description="five spades out of order are a flush",
        cards=SPADE_FLUSH,
        pattern=FLUSH,
        reading=(ACE_OF_SPADES, NINE_OF_SPADES, FIVE_OF_SPADES, THREE_OF_SPADES, TWO_OF_SPADES),
    ),
    StrongestCase(
        description="a run in mixed suits is a straight",
        cards=SIX_HIGH_STRAIGHT,
        pattern=STRAIGHT,
        reading=(TWO_OF_SPADES, THREE_OF_HEARTS, FOUR_OF_CLUBS, FIVE_OF_DIAMONDS, SIX_OF_SPADES),
    ),
    StrongestCase(
        description="three sevens beside two odd cards are a triplet",
        cards=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS, TWO_OF_CLUBS, THREE_OF_HEARTS),
        pattern=TRIPLET,
        reading=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS),
    ),
    StrongestCase(
        description="two kings and two fives are two pair",
        cards=(KING_OF_SPADES, KING_OF_HEARTS, FIVE_OF_SPADES, FIVE_OF_HEARTS, TWO_OF_CLUBS),
        pattern=TWO_PAIR,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, FIVE_OF_SPADES, FIVE_OF_HEARTS),
    ),
    StrongestCase(
        description="two kings alone are a pair",
        cards=KINGS,
        pattern=PAIR,
        reading=(KING_OF_SPADES, KING_OF_HEARTS),
    ),
    StrongestCase(
        description="unrelated cards are the highest of them",
        cards=(KING_OF_SPADES, FIVE_OF_HEARTS, TWO_OF_CLUBS),
        pattern=HIGH_CARD,
        reading=(KING_OF_SPADES,),
    ),
    StrongestCase(description="no cards form nothing", cards=(), pattern=None, reading=None),
)


@pytest.mark.parametrize("case", STRONGEST, ids=descriptions(STRONGEST))
def test_a_ranking_reads_the_best_combination_a_hand_forms(case: StrongestCase) -> None:
    found = POKER.strongest(case.cards)

    assert (found.pattern if found is not None else None) == case.pattern
    assert (found.reading if found is not None else None) == case.reading


@dataclass(frozen=True)
class ContestCase(Case):
    left: tuple[CardOrJoker, ...]
    right: tuple[CardOrJoker, ...]
    comparison: int
    equivalent: bool


CONTESTS: Final[tuple[ContestCase, ...]] = (
    ContestCase(
        description="a straight flush beats a quadruplet",
        left=ROYAL_FLUSH,
        right=FOUR_KINGS,
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="a quadruplet beats a full house",
        left=FOUR_KINGS,
        right=KINGS_OVER_FIVES,
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="a full house beats a flush",
        left=KINGS_OVER_FIVES,
        right=SPADE_FLUSH,
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="a flush beats a straight",
        left=SPADE_FLUSH,
        right=SIX_HIGH_STRAIGHT,
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="a straight beats two pair",
        left=SIX_HIGH_STRAIGHT,
        right=(KING_OF_SPADES, KING_OF_HEARTS, FIVE_OF_SPADES, FIVE_OF_HEARTS, TWO_OF_CLUBS),
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="the higher pair takes the contest",
        left=KINGS,
        right=FIVES,
        comparison=1,
        equivalent=False,
    ),
    ContestCase(
        description="two pairs of kings stand alongside each other",
        left=KINGS,
        right=OTHER_KINGS,
        comparison=0,
        equivalent=True,
    ),
    ContestCase(
        description="the wheel stands below a six-high straight",
        left=WHEEL,
        right=SIX_HIGH_STRAIGHT,
        comparison=-1,
        equivalent=False,
    ),
)


@pytest.mark.parametrize("case", CONTESTS, ids=descriptions(CONTESTS))
def test_a_ranking_settles_one_hand_against_another(case: ContestCase) -> None:
    order = POKER.order
    left = POKER.strongest(case.left)
    right = POKER.strongest(case.right)

    assert left is not None
    assert right is not None
    assert order.compare(left, right) == case.comparison
    assert order.equivalent(left, right) is case.equivalent


def test_a_ranking_picks_the_winners_out_of_a_table() -> None:
    order = POKER.order
    hands = tuple(POKER.strongest(cards) for cards in (FIVES, ROYAL_FLUSH, KINGS))

    assert order.argmaxima(hands) == (1,)
    assert order.argminima(hands) == (0,)


def test_a_ranking_names_every_seat_that_shares_the_top() -> None:
    order = POKER.order
    hands = tuple(POKER.strongest(cards) for cards in (KINGS, FIVES, OTHER_KINGS))

    assert order.argmaxima(hands) == (0, 2)


@dataclass(frozen=True)
class SettledCase(Case):
    left: tuple[CardOrJoker, ...]
    right: tuple[CardOrJoker, ...]
    comparison: int


SETTLED: Final[tuple[SettledCase, ...]] = (
    SettledCase(
        description="the suits settle two pairs of kings",
        left=KINGS,
        right=OTHER_KINGS,
        comparison=1,
    ),
    SettledCase(
        description="the rank of a single card runs before its suit",
        left=(ACE_OF_CLUBS,),
        right=(KING_OF_SPADES,),
        comparison=1,
    ),
    SettledCase(
        description="a pair of fives stands above the ace of spades alone",
        left=FIVES,
        right=(ACE_OF_SPADES, KING_OF_SPADES),
        comparison=1,
    ),
)


@pytest.mark.parametrize("case", SETTLED, ids=descriptions(SETTLED))
def test_a_total_order_settles_the_contests_a_ranking_holds_alongside(case: SettledCase) -> None:
    left = POKER.strongest(case.left)
    right = POKER.strongest(case.right)

    assert left is not None
    assert right is not None
    assert POKER_ORDER.compare(left, right) == case.comparison
    assert POKER_ORDER.compare(right, left) == -case.comparison


def test_a_total_order_gives_every_single_card_and_every_pair_a_place_of_its_own() -> None:
    deck = tuple(Card(rank=rank, suit=suit) for rank in Rank for suit in Suit)
    singles = tuple(find((card,), HIGH_CARD, REGULAR_EVALUATION) for card in deck)
    pairs = tuple(
        find(alike, PAIR, REGULAR_EVALUATION) for alike in combinations(deck, 2) if alike[0].rank == alike[1].rank
    )

    assert all(found is not None for found in singles + pairs)
    single_places = {POKER_ORDER.key(found) for found in singles if found is not None}
    pair_places = {POKER_ORDER.key(found) for found in pairs if found is not None}

    assert len(single_places) == len(deck)
    assert len(pair_places) == len(pairs)
    assert min(pair_places) > max(single_places)


def test_a_ranking_answers_for_the_patterns_it_lists() -> None:
    three_of_a_suit = find((KING_OF_SPADES, NINE_OF_SPADES, TWO_OF_SPADES), THREE_OF_A_SUIT, REGULAR_EVALUATION)

    assert three_of_a_suit is not None
    with pytest.raises(KeyError, match="takes no place"):
        POKER.order.key(three_of_a_suit)


def test_a_ranking_gives_every_pattern_one_place() -> None:
    with pytest.raises(ValidationError, match="Every pattern takes one place"):
        Ranking(patterns=(PAIR, TRIPLET, PAIR), evaluation=REGULAR_EVALUATION)


def test_a_ranking_recognises_a_combination_at_the_least() -> None:
    with pytest.raises(ValidationError, match="at least 1 item"):
        Ranking(patterns=(), evaluation=REGULAR_EVALUATION)


def test_a_ranking_of_its_own_answers_only_the_combinations_it_names() -> None:
    suits_alone = Ranking(patterns=(THREE_OF_A_SUIT,), evaluation=REGULAR_EVALUATION)

    found = suits_alone.strongest((KING_OF_SPADES, NINE_OF_SPADES, TWO_OF_SPADES, ACE_OF_CLUBS))

    assert found is not None
    assert found.pattern == THREE_OF_A_SUIT
    assert suits_alone.strongest((KING_OF_SPADES, NINE_OF_SPADES, ACE_OF_CLUBS)) is None


def test_a_ranking_names_the_counts_its_combinations_take() -> None:
    assert POKER.sizes() == (SINGLE_CARD, PAIR_CARDS, TRIPLET_CARDS, TWO_PAIR_CARDS, POKER_HAND)
    assert ALIKE_ALONE.sizes() == (SINGLE_CARD, PAIR_CARDS, TRIPLET_CARDS)


def test_a_ranking_narrows_to_the_patterns_taking_one_count() -> None:
    of_five = POKER.sized(POKER_HAND)

    assert of_five.patterns == (STRAIGHT, FLUSH, FULL_HOUSE, STRAIGHT_FLUSH)
    assert of_five.evaluation == POKER.evaluation
    assert of_five.sizes() == (POKER_HAND,)


def test_a_ranking_narrowed_to_a_count_reads_that_count_alone() -> None:
    of_two = POKER.sized(PAIR_CARDS)

    assert of_two.strongest(THREE_KINGS) is not None
    assert of_two.strongest((KING_OF_SPADES,)) is None


def test_a_count_no_combination_takes_is_refused_naming_the_counts_that_are() -> None:
    with pytest.raises(KeyError, match="No combination of this ranking takes 6 cards; it takes 1, 2, 3, 4, 5"):
        POKER.sized(PAST_THE_RANKING)


@dataclass(frozen=True)
class WholeCase(Case):
    """One hand beside the combination it is and the combination it holds, which part twice over."""

    cards: tuple[CardOrJoker, ...]
    whole: Pattern | None
    best: Pattern | None


WHOLE: Final[tuple[WholeCase, ...]] = (
    WholeCase(
        description="five spades in a row are a straight flush and hold one",
        cards=ROYAL_FLUSH,
        whole=STRAIGHT_FLUSH,
        best=STRAIGHT_FLUSH,
    ),
    WholeCase(
        description="three kings are a triplet and hold one",
        cards=THREE_KINGS,
        whole=TRIPLET,
        best=TRIPLET,
    ),
    WholeCase(
        description="four kings are a quadruplet and hold one",
        cards=FOUR_KINGS_ALONE,
        whole=QUADRUPLET,
        best=QUADRUPLET,
    ),
    WholeCase(
        description="two kings beside a spare card hold a pair and are none",
        cards=KINGS,
        whole=None,
        best=PAIR,
    ),
    WholeCase(
        description="four kings beside a spare card hold a quadruplet and are none",
        cards=FOUR_KINGS,
        whole=None,
        best=QUADRUPLET,
    ),
    WholeCase(description="no cards are none and hold none", cards=(), whole=None, best=None),
)


@pytest.mark.parametrize("case", WHOLE, ids=descriptions(WHOLE))
def test_a_ranking_reads_a_hand_as_the_combination_it_is_and_as_the_one_it_holds(case: WholeCase) -> None:
    whole = POKER.exactly(case.cards)
    best = POKER.strongest(case.cards)

    assert (whole.pattern if whole is not None else None) == case.whole
    assert (best.pattern if best is not None else None) == case.best


def test_a_hand_reaching_past_every_pattern_of_its_count_is_no_combination() -> None:
    best = ALIKE_ALONE.strongest(FOUR_KINGS_ALONE)

    assert ALIKE_ALONE.exactly(FOUR_KINGS_ALONE) is None
    assert best is not None
    assert best.pattern == TRIPLET


@dataclass(frozen=True)
class ClimbCase(Case):
    challenger: tuple[CardOrJoker, ...]
    held: tuple[CardOrJoker, ...]
    climbs: bool


CLIMBS: Final[tuple[ClimbCase, ...]] = (
    ClimbCase(description="the higher pair climbs over the lower", challenger=KINGS, held=FIVES, climbs=True),
    ClimbCase(description="the lower pair stands below the higher", challenger=FIVES, held=KINGS, climbs=False),
    ClimbCase(
        description="the higher suit climbs over a pair of the same rank",
        challenger=KINGS,
        held=OTHER_KINGS,
        climbs=True,
    ),
    ClimbCase(description="a pair climbs over none reading its own cards", challenger=KINGS, held=KINGS, climbs=False),
    ClimbCase(
        description="a stronger combination of another count stands beside rather than over",
        challenger=ROYAL_FLUSH,
        held=KINGS,
        climbs=False,
    ),
    ClimbCase(
        description="a weaker combination of another count stands beside it as well",
        challenger=KINGS,
        held=ROYAL_FLUSH,
        climbs=False,
    ),
)


@pytest.mark.parametrize("case", CLIMBS, ids=descriptions(CLIMBS))
def test_a_ranking_states_which_combination_climbs_over_another(case: ClimbCase) -> None:
    challenger = POKER.strongest(case.challenger)
    held = POKER.strongest(case.held)

    assert challenger is not None
    assert held is not None
    assert POKER.climbs(challenger, held) is case.climbs


def test_a_ranking_reads_the_best_of_every_count_a_deck_reaches() -> None:
    ceilings = POKER.ceilings(STANDARD_CARDS)

    assert tuple(ceilings) == POKER.sizes()
    assert ceilings[SINGLE_CARD].reading == (ACE_OF_SPADES,)
    assert ceilings[PAIR_CARDS].reading == (ACE_OF_SPADES, ACE_OF_HEARTS)
    assert ceilings[POKER_HAND].pattern == STRAIGHT_FLUSH
    assert ceilings[POKER_HAND].reading == (
        TEN_OF_SPADES,
        JACK_OF_SPADES,
        QUEEN_OF_SPADES,
        KING_OF_SPADES,
        ACE_OF_SPADES,
    )


def test_a_ceiling_stands_over_every_combination_of_its_count_a_hand_forms() -> None:
    ceilings = POKER.ceilings(STANDARD_CARDS)
    kings = POKER.strongest(KINGS)

    assert kings is not None
    assert POKER.climbs(ceilings[PAIR_CARDS], kings)
    assert not POKER.climbs(kings, ceilings[PAIR_CARDS])


def test_a_ranking_names_the_counts_a_deck_reaches() -> None:
    ceilings = FIVES_APART.ceilings(STANDARD_CARDS)

    assert tuple(ceilings) == (PAIR_CARDS,)
    assert FIVES_APART.sizes() == (PAIR_CARDS, POKER_HAND)


def test_a_ranking_offers_every_selection_a_hand_reads_as_a_combination() -> None:
    offered = ALIKE_ALONE.selections(THREE_KINGS)

    assert {tuple(sorted(selection)) for selection in offered} == {
        (0,),
        (1,),
        (2,),
        (0, 1),
        (0, 2),
        (1, 2),
        (0, 1, 2),
    }
    assert len(offered) == len(set(offered))


def test_every_selection_a_ranking_offers_reads_as_a_combination_of_it() -> None:
    hand = (*ROYAL_FLUSH, *THREE_KINGS)

    offered = POKER.selections(hand)

    assert offered
    assert all(POKER.exactly(tuple(hand[place] for place in selection)) is not None for selection in offered)


@dataclass(frozen=True)
class ApartCase(Case):
    """One hand beside the combination each ranking reads it as, the rules of poker with and without spreads.

    `plain` is what the hand comes to where every copy of a card answers for itself, and `apart` is what it comes
    to where the places of a rule each hold a suit or a rank of their own. A row where the two differ is a row a
    second deck made possible, and `reading` is what the apart ranking reads the hand as.
    """

    cards: tuple[CardOrJoker, ...]
    plain: Pattern
    apart: Pattern
    reading: tuple[Card, ...]


APART: Final[tuple[ApartCase, ...]] = (
    ApartCase(
        description="five spades in a row are a straight flush under either ranking",
        cards=ROYAL_FLUSH,
        plain=STRAIGHT_FLUSH,
        apart=STRAIGHT_FLUSH,
        reading=(TEN_OF_SPADES, JACK_OF_SPADES, QUEEN_OF_SPADES, KING_OF_SPADES, ACE_OF_SPADES),
    ),
    ApartCase(
        description="four suits of a rank are a quadruplet under either",
        cards=FOUR_KINGS_ALONE,
        plain=QUADRUPLET,
        apart=APART_QUADRUPLET,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_DIAMONDS, KING_OF_CLUBS),
    ),
    ApartCase(
        description="three suits over two are a full house under either",
        cards=KINGS_OVER_FIVES,
        plain=FULL_HOUSE,
        apart=APART_FULL_HOUSE,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, KING_OF_CLUBS, FIVE_OF_SPADES, FIVE_OF_HEARTS),
    ),
    ApartCase(
        description="two pairs of two suits each are two pair under either",
        cards=TWO_PAIR_OF_TWO_SUITS,
        plain=TWO_PAIR,
        apart=APART_TWO_PAIR,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_SPADES, QUEEN_OF_HEARTS),
    ),
    ApartCase(
        description="a triplet leaning on a card held twice is the pair its two suits reach",
        cards=TRIPLET_LEANING,
        plain=TRIPLET,
        apart=APART_PAIR,
        reading=(KING_OF_SPADES, KING_OF_HEARTS),
    ),
    ApartCase(
        description="one card held twice is a pair, and read apart the one card it shows",
        cards=KING_HELD_TWICE,
        plain=PAIR,
        apart=HIGH_CARD,
        reading=(KING_OF_SPADES,),
    ),
    ApartCase(
        description="two pair leaning on a card held twice are the one pair holding two suits",
        cards=TWO_PAIR_LEANING,
        plain=TWO_PAIR,
        apart=APART_PAIR,
        reading=(QUEEN_OF_SPADES, QUEEN_OF_HEARTS),
    ),
    ApartCase(
        description="a full house leaning on a card held twice comes to two pair read apart",
        cards=FULL_HOUSE_LEANING,
        plain=FULL_HOUSE,
        apart=APART_TWO_PAIR,
        reading=(KING_OF_SPADES, KING_OF_HEARTS, QUEEN_OF_SPADES, QUEEN_OF_HEARTS),
    ),
    ApartCase(
        description="a flush leaning on a card held twice comes to the high card of the suit",
        cards=FLUSH_LEANING,
        plain=FLUSH,
        apart=HIGH_CARD,
        reading=(FIVE_OF_SPADES,),
    ),
)


@pytest.mark.parametrize("case", APART, ids=descriptions(APART))
def test_a_ranking_of_rules_read_apart_reads_a_hand_by_the_facings_it_holds(case: ApartCase) -> None:
    plain = POKER.strongest(case.cards)
    apart = APART_POKER.strongest(case.cards)

    assert plain is not None
    assert apart is not None
    assert plain.pattern == case.plain
    assert apart.pattern == case.apart
    assert apart.reading == case.reading


def test_a_ranking_of_rules_read_apart_orders_a_hand_by_the_combination_its_facings_reach() -> None:
    """The facings a hand holds are what it answers with, and the order follows the combination that makes.

    Both hands are a full house where every copy of a card answers for itself, and the kings take the contest by
    the rank of their triplet. Where the places of a triplet each hold a suit of their own, the kings come to two
    pair and the queens take it, which is the whole of what a game states by ranking the rules read apart.
    """
    plain_kings = POKER.strongest(FULL_HOUSE_LEANING)
    plain_queens = POKER.strongest(QUEENS_OVER_JACKS)
    apart_kings = APART_POKER.strongest(FULL_HOUSE_LEANING)
    apart_queens = APART_POKER.strongest(QUEENS_OVER_JACKS)

    assert plain_kings is not None
    assert plain_queens is not None
    assert apart_kings is not None
    assert apart_queens is not None
    assert POKER_ORDER.compare(plain_kings, plain_queens) == 1
    assert APART_POKER_ORDER.compare(apart_kings, apart_queens) == -1


def test_a_hand_leaning_on_a_card_held_twice_answers_a_ranking_read_apart_at_a_shorter_count() -> None:
    """A rule read apart turns the second copy away, so the hand answers with the count its facings reach.

    These five cards are a full house where every copy answers for itself, and the contest they stand in is one
    of five cards. Where a triplet asks three suits of one rank they are two pair, so they answer at four cards
    and are a combination of five in no way at all.
    """
    plain = POKER.strongest(FULL_HOUSE_LEANING)
    apart = APART_POKER.strongest(FULL_HOUSE_LEANING)

    assert plain is not None
    assert apart is not None
    assert plain.pattern.size == POKER_HAND
    assert apart.pattern.size == TWO_PAIR_CARDS
    assert APART_POKER.exactly(FULL_HOUSE_LEANING) is None


def test_a_ranking_of_rules_read_apart_reads_one_deck_as_the_rules_themselves_do() -> None:
    """Over a deck holding every card once, every card faces apart from every other, so the ceilings coincide.

    A spread turns a card away where another card of the same facing stands at a place of it already, which one
    deck offers nowhere. So the best of every count is the same combination read by the rule holding it apart.
    """
    plain = POKER.ceilings(STANDARD_CARDS)
    apart = APART_POKER.ceilings(STANDARD_CARDS)

    assert APART_POKER.sizes() == POKER.sizes()
    assert tuple(apart) == tuple(plain)
    assert all(apart[size].reading == plain[size].reading for size in plain)
