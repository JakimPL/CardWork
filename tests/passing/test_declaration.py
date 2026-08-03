from dataclasses import dataclass
from random import Random
from typing import Final

import pytest

from cardgames.passing.rules import NOTHING, ROUND_POINT, PassingClaim, declares, four_read_alike, three_read_alike
from cardgames.passing.state import PassingPhase
from cardgames.passing.zones import hand_of
from cardwork.cards.cards import (
    BLACK_JOKER,
    FIVE_OF_HEARTS,
    KING_OF_CLUBS,
    KING_OF_SPADES,
    NINE_OF_DIAMONDS,
    NINE_OF_SPADES,
    RED_JOKER,
    SEVEN_OF_CLUBS,
    SEVEN_OF_DIAMONDS,
    SEVEN_OF_HEARTS,
    SEVEN_OF_SPADES,
    THREE_OF_HEARTS,
    THREE_OF_SPADES,
    TWO_OF_SPADES,
)
from cardwork.cards.game import CardsOrJokers
from cardwork.exceptions import IllegalMove
from cardwork.moves.actions import Declare
from cardwork.moves.move import Move

from ..cases import Case, descriptions
from .driving import (
    FIRST_CARD,
    SEATS,
    SEED,
    PassingGame,
    claim_a_win,
    every_hand,
    held_by,
    play_to_a_claim,
    seat_on_turn,
    until_the_turn_holds_no_win,
)

FIRST_ROUND: Final[int] = 1
ANOTHER_WORD: Final[str] = "bluff"


@dataclass(frozen=True)
class DeclarationCase(Case):
    hand: CardsOrJokers
    three_alike: bool
    four_alike: bool
    declares: bool


DECLARATIONS: Final[tuple[DeclarationCase, ...]] = (
    DeclarationCase(
        description="three of a rank beside an odd card declares",
        hand=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS, KING_OF_CLUBS),
        three_alike=True,
        four_alike=False,
        declares=True,
    ),
    DeclarationCase(
        description="three of a suit beside an odd card declares",
        hand=(KING_OF_SPADES, NINE_OF_SPADES, TWO_OF_SPADES, THREE_OF_HEARTS),
        three_alike=True,
        four_alike=False,
        declares=True,
    ),
    DeclarationCase(
        description="four of a rank holds the win back",
        hand=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS, SEVEN_OF_CLUBS),
        three_alike=True,
        four_alike=True,
        declares=False,
    ),
    DeclarationCase(
        description="four of a suit holds the win back",
        hand=(KING_OF_SPADES, NINE_OF_SPADES, THREE_OF_SPADES, TWO_OF_SPADES),
        three_alike=True,
        four_alike=True,
        declares=False,
    ),
    DeclarationCase(
        description="four cards sharing nothing hold no win",
        hand=(TWO_OF_SPADES, FIVE_OF_HEARTS, NINE_OF_DIAMONDS, KING_OF_CLUBS),
        three_alike=False,
        four_alike=False,
        declares=False,
    ),
    DeclarationCase(
        description="two naturals of a rank beside a joker declare",
        hand=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, RED_JOKER, KING_OF_CLUBS),
        three_alike=True,
        four_alike=False,
        declares=True,
    ),
    DeclarationCase(
        description="two naturals of a suit beside a joker declare",
        hand=(KING_OF_SPADES, NINE_OF_SPADES, RED_JOKER, THREE_OF_HEARTS),
        three_alike=True,
        four_alike=False,
        declares=True,
    ),
    DeclarationCase(
        description="three naturals of a rank beside a joker read alike in four",
        hand=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS, RED_JOKER),
        three_alike=True,
        four_alike=True,
        declares=False,
    ),
    DeclarationCase(
        description="three naturals of a suit beside a joker read alike in four",
        hand=(KING_OF_SPADES, NINE_OF_SPADES, TWO_OF_SPADES, RED_JOKER),
        three_alike=True,
        four_alike=True,
        declares=False,
    ),
    DeclarationCase(
        description="three naturals sharing nothing beside a joker hold no win",
        hand=(TWO_OF_SPADES, FIVE_OF_HEARTS, NINE_OF_DIAMONDS, RED_JOKER),
        three_alike=False,
        four_alike=False,
        declares=False,
    ),
    DeclarationCase(
        description="two naturals sharing neither rank nor suit declare beside two jokers",
        hand=(TWO_OF_SPADES, FIVE_OF_HEARTS, RED_JOKER, BLACK_JOKER),
        three_alike=True,
        four_alike=False,
        declares=True,
    ),
    DeclarationCase(
        description="two naturals of a rank read alike in four beside two jokers",
        hand=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, RED_JOKER, BLACK_JOKER),
        three_alike=True,
        four_alike=True,
        declares=False,
    ),
    DeclarationCase(
        description="two naturals of a suit read alike in four beside two jokers",
        hand=(KING_OF_SPADES, NINE_OF_SPADES, RED_JOKER, BLACK_JOKER),
        three_alike=True,
        four_alike=True,
        declares=False,
    ),
    DeclarationCase(
        description="one natural beside three jokers reads alike in four",
        hand=(TWO_OF_SPADES, RED_JOKER, BLACK_JOKER, RED_JOKER),
        three_alike=True,
        four_alike=True,
        declares=False,
    ),
    DeclarationCase(
        description="four jokers read alike in four",
        hand=(RED_JOKER, RED_JOKER, BLACK_JOKER, BLACK_JOKER),
        three_alike=True,
        four_alike=True,
        declares=False,
    ),
    DeclarationCase(
        description="three cards of one rank fall short of the four a win is read from",
        hand=(SEVEN_OF_SPADES, SEVEN_OF_HEARTS, SEVEN_OF_DIAMONDS),
        three_alike=True,
        four_alike=False,
        declares=False,
    ),
)


@pytest.mark.parametrize("case", DECLARATIONS, ids=descriptions(DECLARATIONS))
def test_a_hand_declares_on_three_reading_alike_while_the_four_do_not(case: DeclarationCase) -> None:
    assert three_read_alike(case.hand) is case.three_alike
    assert four_read_alike(case.hand) is case.four_alike
    assert declares(case.hand) is case.declares


def test_a_claim_the_hand_holds_back_is_refused_and_leaves_the_round_as_it_stood(passing: PassingGame) -> None:
    until_the_turn_holds_no_win(passing)
    standing, hands, head = passing.state, every_hand(passing), passing.head

    with pytest.raises(IllegalMove, match="holds back"):
        claim_a_win(passing)

    assert passing.state == standing
    assert every_hand(passing) == hands
    assert passing.head == head
    assert passing.state.phase == PassingPhase.PASSING


def test_a_claim_in_a_word_the_game_leaves_out_is_refused_and_leaves_the_round_as_it_stood(
    passing: PassingGame,
) -> None:
    seat = seat_on_turn(passing)
    standing, hands, head = passing.state, every_hand(passing), passing.head

    with pytest.raises(IllegalMove, match=ANOTHER_WORD):
        passing.submit(
            Move(player=seat, action=Declare(claim=ANOTHER_WORD, indices=frozenset())),
            base_seq=passing.head,
        )

    assert passing.state == standing
    assert every_hand(passing) == hands
    assert passing.head == head


def test_a_claim_of_part_of_the_hand_is_refused_and_leaves_the_round_as_it_stood(passing: PassingGame) -> None:
    seat = seat_on_turn(passing)
    standing, hands, head = passing.state, every_hand(passing), passing.head

    with pytest.raises(IllegalMove, match="whole hand"):
        passing.submit(
            Move(player=seat, action=Declare(claim=PassingClaim.WIN, indices=frozenset({FIRST_CARD}))),
            base_seq=passing.head,
        )

    assert passing.state == standing
    assert every_hand(passing) == hands
    assert passing.head == head


def test_a_confirmed_claim_decides_the_round_and_shows_the_hand_it_was_made_from(passing: PassingGame) -> None:
    winner = play_to_a_claim(passing, Random(SEED).choice)

    assert passing.state.phase == PassingPhase.DECIDED
    assert passing.state.winner == winner
    assert passing.state.to_act == frozenset()
    assert passing.state.round_points == tuple(ROUND_POINT if seat == winner else NOTHING for seat in range(SEATS))
    assert declares(held_by(passing, winner))
    assert all(not game_card.face_down for game_card in passing.board.zone(hand_of(winner)).cards)


def test_the_table_reads_the_hand_a_confirmed_claim_was_made_from(passing: PassingGame) -> None:
    winner = play_to_a_claim(passing, Random(SEED).choice)
    onlooker = (winner + 1) % SEATS

    view = passing.view(observer=onlooker)

    assert view.zones[hand_of(winner)].cards == passing.board.zone(hand_of(winner)).cards


def test_the_round_a_claim_won_is_scored_into_the_standing_and_the_next_one_dealt(passing: PassingGame) -> None:
    winner = play_to_a_claim(passing, Random(SEED).choice)
    leader = passing.state.led_by

    passing.settle()

    assert passing.state.points == tuple(ROUND_POINT if seat == winner else NOTHING for seat in range(SEATS))
    assert passing.state.phase == PassingPhase.PASSING
    assert passing.state.round_number > FIRST_ROUND
    assert passing.state.led_by == (leader + 1) % SEATS
    assert passing.state.winner is None
    assert passing.state.round_points == (NOTHING,) * SEATS
