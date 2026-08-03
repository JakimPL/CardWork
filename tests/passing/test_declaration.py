from dataclasses import dataclass
from random import Random
from typing import Final

import pytest

from cardgames.passing.rules import NOTHING, ROUND_POINT, declares, four_read_alike, three_read_alike
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

from ..cases import Case, descriptions
from .driving import (
    JOKERED_DECK,
    SEATS,
    SEED,
    PassingGame,
    a_match,
    held_by,
    play_to_a_win,
)

FIRST_ROUND: Final[int] = 1
SEEDS: Final[range] = range(40)


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


def test_a_hand_that_wins_decides_its_round_and_shows_the_cards_it_won_with(passing: PassingGame) -> None:
    winner = play_to_a_win(passing, Random(SEED).choice)

    assert passing.state.phase == PassingPhase.DECIDED
    assert passing.state.winner == winner
    assert passing.state.to_act == frozenset()
    assert passing.state.round_points == tuple(ROUND_POINT if seat == winner else NOTHING for seat in range(SEATS))
    assert declares(held_by(passing, winner))
    assert all(not game_card.face_down for game_card in passing.board.zone(hand_of(winner)).cards)


def test_the_table_reads_the_hand_a_round_was_won_with(passing: PassingGame) -> None:
    winner = play_to_a_win(passing, Random(SEED).choice)
    onlooker = (winner + 1) % SEATS

    view = passing.view(observer=onlooker)

    assert view.zones[hand_of(winner)].cards == passing.board.zone(hand_of(winner)).cards


def test_a_win_lands_in_the_transaction_of_the_move_that_completed_the_hand(passing: PassingGame) -> None:
    """A move leaving a winning hand behind carries the award, so no window of latency comes between them."""
    winner = play_to_a_win(passing, Random(SEED).choice)
    deciding = passing.journal.transactions[passing.head - 1]

    assert deciding.move is not None
    assert passing.snapshot(passing.head - 1).state.winner is None
    assert passing.snapshot(passing.head).state.winner == winner


def test_the_round_a_win_took_is_scored_into_the_standing_and_the_next_one_dealt(passing: PassingGame) -> None:
    winner = play_to_a_win(passing, Random(SEED).choice)
    standing, leader = passing.state.points, passing.state.led_by
    assert standing is not None

    passing.settle()

    assert passing.state.points == tuple(
        scored + (ROUND_POINT if seat == winner else NOTHING) for seat, scored in enumerate(standing)
    )
    assert passing.state.phase == PassingPhase.PASSING
    assert passing.state.round_number > FIRST_ROUND
    assert passing.state.led_by == (leader + 1) % SEATS
    assert passing.state.winner is None
    assert passing.state.round_points == (NOTHING,) * SEATS


def test_a_seat_offered_a_move_is_never_holding_a_win(passing: PassingGame) -> None:
    """The turn stands only with a hand holding no win, which is what leaves the award nothing to decide."""
    chooser = Random(SEED)
    while True:
        moves = passing.legal_moves(passing.position)
        if not moves:
            if not passing.settle():
                return

            continue

        seat = passing.state.current
        assert seat is not None
        assert not declares(held_by(passing, seat))
        passing.submit(chooser.choice(moves), base_seq=passing.head)


@pytest.mark.parametrize("seed", SEEDS)
def test_a_deal_reading_a_win_decides_its_round_before_a_seat_acts(seed: int) -> None:
    """A table opens on a round with a turn to take, whatever the deal it was given.

    A fourth card dealt into three that read alike wins where no seat has yet acted, and the table settles that
    round away as it is built, so every driver beyond this finds a seat on turn holding no win.
    """
    game = a_match(SEATS, JOKERED_DECK, seed)

    assert game.state.phase == PassingPhase.PASSING
    assert game.state.current is not None
    assert not declares(held_by(game, game.state.current))
    assert game.legal_moves(game.position) != ()
