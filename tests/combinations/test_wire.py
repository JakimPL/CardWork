from abc import ABC
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Final, Literal

import pytest
from pydantic import ValidationError

from cardwork.cards.cards import (
    KING_OF_HEARTS,
    KING_OF_SPADES,
    QUEEN_OF_SPADES,
    TEN_OF_SPADES,
    TWO_OF_HEARTS,
)
from cardwork.cards.game import CardsOrJokers
from cardwork.cards.suit import Suit
from cardwork.combinations.combination import Combination
from cardwork.combinations.demand import ANY_CARD
from cardwork.combinations.detect import find
from cardwork.combinations.pattern import Pattern, Reading
from cardwork.combinations.patterns.any_cards import AnyCards
from cardwork.combinations.patterns.apart import Apart
from cardwork.combinations.patterns.beside import Beside
from cardwork.combinations.patterns.run import Run
from cardwork.combinations.patterns.same_rank import SameRank
from cardwork.combinations.patterns.simple import Simple
from cardwork.combinations.patterns.together import Together
from cardwork.combinations.poker import (
    APART_PAIR,
    APART_POKER,
    APART_TWO_PAIR,
    FULL_HOUSE,
    HIGH_CARD,
    PAIR,
    POKER,
    STRAIGHT,
    STRAIGHT_FLUSH,
    TRIPLET,
    TWO_PAIR,
)
from cardwork.combinations.policy import REGULAR_EVALUATION, Evaluation
from cardwork.combinations.ranking import Ranking
from cardwork.combinations.shape import Shape
from cardwork.combinations.spread import Facet
from cardwork.ordering.preorder import Key
from tests.cases import Case, descriptions

from .authored import OneSuit

SUITED_PLACES: Final[int] = 3
KING_PLACE: Final[int] = REGULAR_EVALUATION.rank_places()[KING_OF_SPADES.rank]
SPADES: Final[CardsOrJokers] = (KING_OF_SPADES, QUEEN_OF_SPADES, TEN_OF_SPADES)
SPADES_AND_A_HEART: Final[CardsOrJokers] = (*SPADES, TWO_OF_HEARTS)
THREE_SPADES: Final[Pattern] = OneSuit(suit=Suit.SPADE, places=SUITED_PLACES)
AUTHORED_INSIDE_A_BUILT_IN: Final[Pattern] = Beside(parts=(THREE_SPADES, PAIR))
CONTRACT: Final[Ranking] = Ranking(
    patterns=(HIGH_CARD, PAIR, THREE_SPADES, AUTHORED_INSIDE_A_BUILT_IN),
    evaluation=REGULAR_EVALUATION,
)
PAIR_OF_KINGS: Final[Combination] = Combination(
    pattern=PAIR,
    cards=(KING_OF_SPADES, KING_OF_HEARTS),
    reading=(KING_OF_SPADES, KING_OF_HEARTS),
    strength=(KING_PLACE, KING_PLACE),
    low_ace=False,
)


class Loose(Simple, ABC):
    """Places any card fills, leaving its own words to the rule that states them.

    A rule holding to this adds a word and a sentence and nothing else, which is the ground the tests of the
    words themselves stand on. Its own words being left open is what keeps it out of the rules in play.
    """

    @property
    def alike(self) -> bool:
        return True

    def shapes(self, evaluation: Evaluation) -> Iterator[Shape]:
        yield Shape(demands=(ANY_CARD,) * self.places, low_ace=False)

    def strength(self, reading: Reading, evaluation: Evaluation) -> Key:
        return self._descending_ranks(reading, evaluation)


@dataclass(frozen=True)
class RoundTripCase(Case):
    """One pattern and the class its word reads back to."""

    pattern: Pattern
    reads_as: type[Pattern]


ROUND_TRIPS: Final[tuple[RoundTripCase, ...]] = (
    RoundTripCase(description="loose places", pattern=HIGH_CARD, reads_as=AnyCards),
    RoundTripCase(description="a rank", pattern=PAIR, reads_as=SameRank),
    RoundTripCase(description="a run", pattern=STRAIGHT, reads_as=Run),
    RoundTripCase(description="parts standing beside each other", pattern=TWO_PAIR, reads_as=Beside),
    RoundTripCase(description="parts read together", pattern=STRAIGHT_FLUSH, reads_as=Together),
    RoundTripCase(description="a rule read apart", pattern=APART_PAIR, reads_as=Apart),
    RoundTripCase(description="rules read apart standing beside each other", pattern=APART_TWO_PAIR, reads_as=Beside),
    RoundTripCase(description="a game's own rule", pattern=THREE_SPADES, reads_as=OneSuit),
    RoundTripCase(
        description="a game's own rule inside a built-in one",
        pattern=AUTHORED_INSIDE_A_BUILT_IN,
        reads_as=Beside,
    ),
)


@pytest.mark.parametrize("case", ROUND_TRIPS, ids=descriptions(ROUND_TRIPS))
def test_a_rule_reads_back_as_the_pattern_its_word_names(case: RoundTripCase) -> None:
    listed = Ranking(patterns=(case.pattern,), evaluation=REGULAR_EVALUATION)

    restored = Ranking.model_validate_json(listed.model_dump_json())

    assert restored == listed
    assert isinstance(restored.patterns[0], case.reads_as)
    assert str(restored.patterns[0]) == str(case.pattern)


def test_a_combination_reads_back_as_the_cards_and_the_rule_it_went_out_as() -> None:
    restored = Combination.model_validate_json(PAIR_OF_KINGS.model_dump_json())

    assert restored == PAIR_OF_KINGS
    assert restored.pattern == PAIR


def test_a_combination_of_a_game_s_own_rule_reads_back_as_that_rule() -> None:
    found = find(SPADES, THREE_SPADES, REGULAR_EVALUATION)
    assert found is not None

    restored = Combination.model_validate_json(found.model_dump_json())

    assert restored == found
    assert isinstance(restored.pattern, OneSuit)
    assert str(restored) == "3 of ♠: K♠ Q♠ 10♠"


def test_a_ranking_a_game_states_of_its_own_rules_reads_back_as_the_ranking_it_is() -> None:
    restored = Ranking.model_validate_json(CONTRACT.model_dump_json())
    found = restored.strongest(SPADES_AND_A_HEART)

    assert restored == CONTRACT
    assert found is not None
    assert found.pattern == THREE_SPADES


def test_the_ranking_this_package_states_reads_back_as_itself() -> None:
    restored = Ranking.model_validate_json(POKER.model_dump_json())

    assert restored == POKER
    assert restored.patterns[-1] == STRAIGHT_FLUSH


def test_a_ranking_of_rules_read_apart_carries_the_facing_each_of_them_holds_apart() -> None:
    restored = Ranking.model_validate_json(APART_POKER.model_dump_json())

    assert restored == APART_POKER
    assert restored.patterns[1] == APART_PAIR


def test_a_pattern_states_the_word_it_travels_under_beside_its_own_fields() -> None:
    assert THREE_SPADES.model_dump() == {"kind": "one_suit", "suit": Suit.SPADE, "places": SUITED_PLACES}
    assert FULL_HOUSE.model_dump() == {
        "kind": "beside",
        "parts": (
            {"kind": "same_rank", "places": TRIPLET.size},
            {"kind": "same_rank", "places": PAIR.size},
        ),
    }
    assert APART_PAIR.model_dump() == {
        "kind": "apart",
        "part": {"kind": "same_rank", "places": PAIR.size},
        "facet": Facet.SUIT,
    }


def test_a_word_names_the_rule_that_states_it() -> None:
    assert Pattern.named("same_rank") is SameRank
    assert Pattern.named("one_suit") is OneSuit


def test_a_word_no_rule_in_play_states_is_refused_naming_the_rules_that_are() -> None:
    with pytest.raises(ValueError, match=r"No rule travels under 'canasta'; the rules in play are .*same_rank"):
        Pattern.named("canasta")


def test_a_pattern_naming_a_rule_out_of_play_is_refused_where_it_is_read() -> None:
    with pytest.raises(ValidationError, match="No rule travels under 'canasta'"):
        Ranking.model_validate({"patterns": [{"kind": "canasta", "places": 3}], "evaluation": REGULAR_EVALUATION})


def test_a_pattern_naming_its_rule_by_no_word_is_refused() -> None:
    with pytest.raises(ValidationError, match="names the rule it is by a word, and this one carries None"):
        Ranking.model_validate({"patterns": [{"places": 3}], "evaluation": REGULAR_EVALUATION})


def test_a_pattern_given_as_itself_stands_as_the_rule_it_already_is() -> None:
    assert Ranking(patterns=(THREE_SPADES,), evaluation=REGULAR_EVALUATION).patterns == (THREE_SPADES,)


def test_a_rule_ready_to_be_read_states_a_word_of_its_own() -> None:
    with pytest.raises(TypeError, match="Wordless is read back by the word naming its rule, and it states none"):

        class Wordless(Loose):
            def __str__(self) -> str:
                return "a rule stating no word"


def test_a_word_stands_for_one_rule_alone() -> None:
    with pytest.raises(TypeError, match="'same_rank' already names SameRank, and Shadowing states it as well"):

        class Shadowing(Loose):
            kind: Literal["same_rank"] = "same_rank"

            def __str__(self) -> str:
                return "a rule under a word another rule already travels under"
