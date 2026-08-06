from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.cards.card import Card, Facing
from cardwork.cards.cards import KING_OF_HEARTS, KING_OF_SPADES
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.combinations.demand import ANY_CARD, Demand
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.patterns.any_cards import AnyCards
from cardwork.combinations.patterns.apart import Apart
from cardwork.combinations.patterns.beside import Beside
from cardwork.combinations.patterns.run import Run
from cardwork.combinations.patterns.same_suit import SameSuit
from cardwork.combinations.patterns.together import Together
from cardwork.combinations.poker import FLUSH, HIGH_CARD, PAIR, STRAIGHT, TWO_PAIR
from cardwork.combinations.policy import REGULAR_EVALUATION
from cardwork.combinations.shape import Shape
from cardwork.combinations.spread import Facet, Spread
from tests.cases import Case, descriptions

FIRST_PAIR: Final[Spread] = Spread(facet=Facet.SUIT, places=frozenset({0, 1}))
SECOND_PAIR: Final[Spread] = Spread(facet=Facet.SUIT, places=frozenset({2, 3}))
BY_CARD: Final[Spread] = Spread(facet=Facet.CARD, places=frozenset({0, 1}))

TWO_KINGS: Final[Shape] = Shape(demands=(Demand.of_rank(Rank.KING),) * 2, low_ace=False)
TWO_QUEENS: Final[Shape] = Shape(demands=(Demand.of_rank(Rank.QUEEN),) * 2, low_ace=False)
TWO_LOOSE: Final[Shape] = Shape(demands=(ANY_CARD,) * 2, low_ace=False)
TWO_KINGS_APART: Final[Shape] = Shape(demands=TWO_KINGS.demands, low_ace=False, spreads=(FIRST_PAIR,))
TWO_QUEENS_APART: Final[Shape] = Shape(demands=TWO_QUEENS.demands, low_ace=False, spreads=(FIRST_PAIR,))
TWO_LOOSE_APART: Final[Shape] = Shape(demands=TWO_LOOSE.demands, low_ace=False, spreads=(BY_CARD,))

APART_PAIR: Final[Pattern] = Apart.of_suit(PAIR)
TWO_APART_PAIRS: Final[Pattern] = Beside(parts=(APART_PAIR, APART_PAIR))
RUN_OF_FOUR: Final[Pattern] = Run(places=4)


@dataclass(frozen=True)
class FacetCase(Case):
    """One card as the facet a spread reads of it, which is what the places of that spread hold apart."""

    facet: Facet
    card: Card
    facing: Facing


FACETS: Final[tuple[FacetCase, ...]] = (
    FacetCase(
        description="a spread by card reads the card itself",
        facet=Facet.CARD,
        card=KING_OF_SPADES,
        facing=KING_OF_SPADES,
    ),
    FacetCase(
        description="a spread by rank reads the rank alone",
        facet=Facet.RANK,
        card=KING_OF_SPADES,
        facing=Rank.KING,
    ),
    FacetCase(
        description="a spread by suit reads the suit alone",
        facet=Facet.SUIT,
        card=KING_OF_SPADES,
        facing=Suit.SPADE,
    ),
    FacetCase(
        description="two cards of one rank face apart by suit",
        facet=Facet.SUIT,
        card=KING_OF_HEARTS,
        facing=Suit.HEART,
    ),
    FacetCase(
        description="two cards of one rank face alike by rank",
        facet=Facet.RANK,
        card=KING_OF_HEARTS,
        facing=Rank.KING,
    ),
)


@pytest.mark.parametrize("case", FACETS, ids=descriptions(FACETS))
def test_a_spread_reads_the_facet_it_holds_its_places_to(case: FacetCase) -> None:
    spread = Spread(facet=case.facet, places=frozenset({0, 1}))

    assert spread.read(case.card) == case.facing


def test_a_spread_names_the_places_that_read_apart() -> None:
    assert FIRST_PAIR.holds(0) is True
    assert FIRST_PAIR.holds(1) is True
    assert FIRST_PAIR.holds(2) is False
    assert FIRST_PAIR.shifted(2) == SECOND_PAIR
    assert FIRST_PAIR.shifted(0) == FIRST_PAIR


def test_readings_standing_beside_each_other_carry_their_spreads_over_the_places_they_take() -> None:
    joined = Shape.beside((TWO_KINGS_APART, TWO_QUEENS_APART))

    assert joined.spreads == (FIRST_PAIR, SECOND_PAIR)
    assert Shape.beside((TWO_KINGS, TWO_QUEENS_APART)).spreads == (SECOND_PAIR,)
    assert Shape.beside((TWO_KINGS, TWO_QUEENS)).spreads == ()


def test_readings_taken_together_carry_their_spreads_over_the_places_they_share() -> None:
    shared = Shape.together((TWO_LOOSE_APART, TWO_KINGS))

    assert shared is not None
    assert shared.demands == TWO_KINGS.demands
    assert shared.spreads == (BY_CARD,)


@dataclass(frozen=True)
class RefusedShapeCase(Case):
    """One reading whose spreads leave a place reading apart in a way the filling cannot hold it to."""

    demands: tuple[Demand, ...]
    spreads: tuple[Spread, ...]
    complaint: str


REFUSED_SHAPES: Final[tuple[RefusedShapeCase, ...]] = (
    RefusedShapeCase(
        description="a spread names a place the reading holds",
        demands=TWO_KINGS.demands,
        spreads=(Spread(facet=Facet.CARD, places=frozenset({0, 2})),),
        complaint=r"reading of 2 places reads apart within them, and \(2,\) stand out",
    ),
    RefusedShapeCase(
        description="a place reads apart one way",
        demands=TWO_KINGS.demands,
        spreads=(FIRST_PAIR, BY_CARD),
        complaint=r"place reads apart one way, and \(0, 1\) read apart more than one",
    ),
    RefusedShapeCase(
        description="spreads overlapping on one place alone are held apart likewise",
        demands=(Demand.of_rank(Rank.KING),) * 3,
        spreads=(
            Spread(facet=Facet.CARD, places=frozenset({0, 1})),
            Spread(facet=Facet.SUIT, places=frozenset({1, 2})),
        ),
        complaint=r"place reads apart one way, and \(1,\) read apart more than one",
    ),
)


@pytest.mark.parametrize("case", REFUSED_SHAPES, ids=descriptions(REFUSED_SHAPES))
def test_a_reading_holds_each_of_its_places_to_one_spread(case: RefusedShapeCase) -> None:
    with pytest.raises(ValueError, match=case.complaint):
        Shape(demands=case.demands, low_ace=False, spreads=case.spreads)


@dataclass(frozen=True)
class ApartShapesCase(Case):
    """One rule read apart beside the readings it admits, each of them holding its places apart."""

    pattern: Apart
    size: int
    shapes: int
    spread: Spread


APART_SHAPES: Final[tuple[ApartShapesCase, ...]] = (
    ApartShapesCase(
        description="a pair apart by suit reads one way per rank, as a pair does",
        pattern=Apart.of_suit(PAIR),
        size=2,
        shapes=len(Rank),
        spread=Spread(facet=Facet.SUIT, places=frozenset({0, 1})),
    ),
    ApartShapesCase(
        description="a pair apart by card reads one way per rank likewise",
        pattern=Apart.of_card(PAIR),
        size=2,
        shapes=len(Rank),
        spread=Spread(facet=Facet.CARD, places=frozenset({0, 1})),
    ),
    ApartShapesCase(
        description="a flush apart by rank reads one way per suit",
        pattern=Apart.of_rank(FLUSH),
        size=5,
        shapes=len(Suit),
        spread=Spread(facet=Facet.RANK, places=frozenset({0, 1, 2, 3, 4})),
    ),
    ApartShapesCase(
        description="two loose places apart by card read one way",
        pattern=Apart.of_card(AnyCards(places=2)),
        size=2,
        shapes=1,
        spread=Spread(facet=Facet.CARD, places=frozenset({0, 1})),
    ),
    ApartShapesCase(
        description="two pair apart by card read one way per pair of ranks",
        pattern=Apart.of_card(TWO_PAIR),
        size=4,
        shapes=len(Rank) * (len(Rank) - 1) // 2,
        spread=Spread(facet=Facet.CARD, places=frozenset({0, 1, 2, 3})),
    ),
    ApartShapesCase(
        description="a run apart by card reads one way per stretch, the wheel besides",
        pattern=Apart.of_card(STRAIGHT),
        size=5,
        shapes=len(Rank) - 5 + 2,
        spread=Spread(facet=Facet.CARD, places=frozenset({0, 1, 2, 3, 4})),
    ),
)


@pytest.mark.parametrize("case", APART_SHAPES, ids=descriptions(APART_SHAPES))
def test_a_rule_read_apart_admits_the_readings_its_part_does(case: ApartShapesCase) -> None:
    admitted = tuple(case.pattern.shapes(REGULAR_EVALUATION))
    stated = tuple(case.pattern.part.shapes(REGULAR_EVALUATION))

    assert case.pattern.size == case.size
    assert len(admitted) == case.shapes
    assert len(admitted) == len(stated)
    assert all(shape.spreads == (case.spread,) for shape in admitted)
    assert tuple(shape.demands for shape in admitted) == tuple(shape.demands for shape in stated)


def test_two_rules_read_apart_standing_beside_each_other_hold_each_of_them_apart_on_its_own() -> None:
    admitted = tuple(TWO_APART_PAIRS.shapes(REGULAR_EVALUATION))

    assert len(admitted) == len(Rank) * (len(Rank) - 1) // 2
    assert all(shape.spreads == (FIRST_PAIR, SECOND_PAIR) for shape in admitted)


def test_a_rule_read_apart_stands_where_its_part_stands() -> None:
    reading = (KING_OF_SPADES, KING_OF_HEARTS)

    assert APART_PAIR.strength(reading, REGULAR_EVALUATION) == PAIR.strength(reading, REGULAR_EVALUATION)


@dataclass(frozen=True)
class ApartWordsCase(Case):
    pattern: Pattern
    words: str


APART_WORDS: Final[tuple[ApartWordsCase, ...]] = (
    ApartWordsCase(description="a pair of two suits", pattern=APART_PAIR, words="2 of a rank apart by suit"),
    ApartWordsCase(
        description="a pair of two cards",
        pattern=Apart.of_card(PAIR),
        words="2 of a rank apart by card",
    ),
    ApartWordsCase(
        description="a flush of five ranks",
        pattern=Apart.of_rank(FLUSH),
        words="5 of a suit apart by rank",
    ),
    ApartWordsCase(
        description="two loose places of two cards",
        pattern=Apart.of_card(AnyCards(places=2)),
        words="any 2 cards apart by card",
    ),
    ApartWordsCase(
        description="two pair holding no card twice",
        pattern=Apart.of_card(TWO_PAIR),
        words="2 of a rank beside 2 of a rank apart by card",
    ),
    ApartWordsCase(
        description="two pair each of two suits",
        pattern=TWO_APART_PAIRS,
        words="2 of a rank apart by suit beside 2 of a rank apart by suit",
    ),
)


@pytest.mark.parametrize("case", APART_WORDS, ids=descriptions(APART_WORDS))
def test_a_rule_read_apart_states_itself_in_words(case: ApartWordsCase) -> None:
    assert str(case.pattern) == case.words
    assert repr(case.pattern) == case.words


@dataclass(frozen=True)
class RefusedApartCase(Case):
    """One rule a spread reads over that the filling settles no reading of, refused as the rule is stated."""

    part: Pattern
    facet: Facet
    complaint: str


REFUSED_APARTS: Final[tuple[RefusedApartCase, ...]] = (
    RefusedApartCase(
        description="one place reads apart from nothing",
        part=HIGH_CARD,
        facet=Facet.CARD,
        complaint="Places read apart from 2 of them upwards, and this rule takes 1",
    ),
    RefusedApartCase(
        description="a rule read apart twice over holds its places apart once",
        part=Apart.of_suit(PAIR),
        facet=Facet.CARD,
        complaint="place reads apart one way, and 2 of a rank apart by suit holds places apart already",
    ),
    RefusedApartCase(
        description="a rule whose parts read apart holds the whole and the parts apart at once",
        part=TWO_APART_PAIRS,
        facet=Facet.SUIT,
        complaint="place reads apart one way, and .* holds places apart already",
    ),
    RefusedApartCase(
        description="two pair ask for two ranks, so one suit answers some of their places alone",
        part=TWO_PAIR,
        facet=Facet.SUIT,
        complaint="spread by suit reads over places asking alike, and 2 of a rank beside 2 of a rank asks",
    ),
    RefusedApartCase(
        description="a run asks each place for a rank of its own, so one suit answers some of them alone",
        part=RUN_OF_FOUR,
        facet=Facet.SUIT,
        complaint="spread by suit reads over places asking alike, and a run of 4 asks",
    ),
    RefusedApartCase(
        description="a run read apart by rank asks differently of its places likewise",
        part=RUN_OF_FOUR,
        facet=Facet.RANK,
        complaint="spread by rank reads over places asking alike, and a run of 4 asks",
    ),
)


@pytest.mark.parametrize("case", REFUSED_APARTS, ids=descriptions(REFUSED_APARTS))
def test_a_rule_a_spread_settles_no_reading_of_is_refused_as_it_is_stated(case: RefusedApartCase) -> None:
    with pytest.raises(ValidationError, match=case.complaint):
        Apart(part=case.part, facet=case.facet)


def test_two_rules_read_apart_are_refused_from_being_read_together() -> None:
    with pytest.raises(ValidationError, match="Places read apart one way, and these parts each hold them apart"):
        Together(parts=(Apart.of_rank(AnyCards(places=2)), Apart.of_suit(AnyCards(places=2))))


@dataclass(frozen=True)
class AlikeCase(Case):
    """One rule beside whether every place of every reading it admits asks the same of the card filling it."""

    pattern: Pattern
    alike: bool


ALIKE: Final[tuple[AlikeCase, ...]] = (
    AlikeCase(description="a pair asks one rank of both places", pattern=PAIR, alike=True),
    AlikeCase(description="a flush asks one suit of every place", pattern=FLUSH, alike=True),
    AlikeCase(description="loose places ask for any card alike", pattern=AnyCards(places=3), alike=True),
    AlikeCase(description="a run asks each place for a rank of its own", pattern=RUN_OF_FOUR, alike=False),
    AlikeCase(description="parts standing beside each other ask their own", pattern=TWO_PAIR, alike=False),
    AlikeCase(
        description="parts read together ask alike where each of them does",
        pattern=Together(parts=(PAIR, SameSuit(places=2))),
        alike=True,
    ),
    AlikeCase(
        description="a suited run asks each place for a card of its own",
        pattern=Together(parts=(RUN_OF_FOUR, SameSuit(places=4))),
        alike=False,
    ),
    AlikeCase(description="a rule read apart asks what its part asks", pattern=APART_PAIR, alike=True),
)


@pytest.mark.parametrize("case", ALIKE, ids=descriptions(ALIKE))
def test_a_rule_states_whether_its_places_ask_alike(case: AlikeCase) -> None:
    assert case.pattern.alike is case.alike


def test_a_rule_states_whether_it_holds_any_of_its_places_apart() -> None:
    assert PAIR.spread is False
    assert TWO_PAIR.spread is False
    assert APART_PAIR.spread is True
    assert TWO_APART_PAIRS.spread is True
    assert Together(parts=(APART_PAIR, SameSuit(places=2))).spread is True


def test_a_rule_read_apart_stands_as_the_rule_its_part_and_facet_state() -> None:
    assert Apart.of_suit(PAIR) == Apart(part=PAIR, facet=Facet.SUIT)
    assert Apart.of_suit(PAIR) != Apart.of_card(PAIR)
    assert Apart.of_suit(PAIR) != PAIR
    assert len({Apart.of_suit(PAIR), Apart(part=PAIR, facet=Facet.SUIT), Apart.of_card(PAIR)}) == 2
