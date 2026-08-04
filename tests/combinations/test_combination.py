from dataclasses import dataclass
from typing import Final

import pytest
from pydantic import ValidationError

from cardwork.cards.card import Card
from cardwork.cards.cards import KING_OF_HEARTS, KING_OF_SPADES, RED_JOKER
from cardwork.cards.game import CardOrJoker
from cardwork.combinations.combination import BY_STRENGTH, Combination
from cardwork.combinations.pattern import Pattern
from cardwork.combinations.poker import PAIR, TRIPLET
from cardwork.combinations.policy import REGULAR_EVALUATION
from tests.cases import Case, descriptions

KING_PLACE: Final[int] = REGULAR_EVALUATION.rank_places()[KING_OF_SPADES.rank]
PAIR_OF_KINGS: Final[Combination] = Combination(
    pattern=PAIR,
    cards=(KING_OF_SPADES, KING_OF_HEARTS),
    reading=(KING_OF_SPADES, KING_OF_HEARTS),
    strength=(KING_PLACE, KING_PLACE),
    low_ace=False,
)


def test_a_combination_reads_as_its_pattern_and_the_cards_that_make_it() -> None:
    assert str(PAIR_OF_KINGS) == "2 of a rank: K♠ K♥"
    assert repr(PAIR_OF_KINGS) == str(PAIR_OF_KINGS)


def test_a_joker_shows_as_itself_beside_the_card_it_stands_for() -> None:
    stood_in = Combination(
        pattern=PAIR,
        cards=(KING_OF_SPADES, RED_JOKER),
        reading=(KING_OF_SPADES, KING_OF_HEARTS),
        strength=(KING_PLACE, KING_PLACE),
        low_ace=False,
    )

    assert str(stood_in) == "2 of a rank: K♠ *♥"
    assert stood_in.reading[1] == KING_OF_HEARTS


def test_combinations_of_one_strength_stand_alongside_each_other() -> None:
    lower = PAIR_OF_KINGS.model_copy(update={"strength": (KING_PLACE - 1, KING_PLACE - 1)})

    assert BY_STRENGTH.equivalent(PAIR_OF_KINGS, PAIR_OF_KINGS.model_copy())
    assert BY_STRENGTH.compare(PAIR_OF_KINGS, lower) == 1
    assert BY_STRENGTH.maxima((lower, PAIR_OF_KINGS)) == (PAIR_OF_KINGS,)


@dataclass(frozen=True)
class RefusedCase(Case):
    pattern: Pattern
    cards: tuple[CardOrJoker, ...]
    reading: tuple[Card, ...]
    complaint: str


REFUSED: Final[tuple[RefusedCase, ...]] = (
    RefusedCase(
        description="a card left without a reading",
        pattern=PAIR,
        cards=(KING_OF_SPADES, KING_OF_HEARTS),
        reading=(KING_OF_SPADES,),
        complaint="Every card reads as one card",
    ),
    RefusedCase(
        description="fewer cards than the pattern takes",
        pattern=TRIPLET,
        cards=(KING_OF_SPADES, KING_OF_HEARTS),
        reading=(KING_OF_SPADES, KING_OF_HEARTS),
        complaint="takes 3 cards",
    ),
)


@pytest.mark.parametrize("case", REFUSED, ids=descriptions(REFUSED))
def test_a_combination_fills_every_place_its_pattern_names(case: RefusedCase) -> None:
    with pytest.raises(ValidationError, match=case.complaint):
        Combination(
            pattern=case.pattern,
            cards=case.cards,
            reading=case.reading,
            strength=(KING_PLACE,),
            low_ace=False,
        )
