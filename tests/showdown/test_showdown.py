from dataclasses import dataclass
from typing import Final

import pytest

from cardgames.backend.showdown.game import ShowdownGame
from cardgames.backend.showdown.rules import NOTHING, awarded, suited, taken_by, turn_points
from cardgames.backend.showdown.zones import DISCARD, Holding, tray_of
from cardwork.cards.card import Cards
from cardwork.cards.cards import (
    ACE_OF_CLUBS,
    ACE_OF_SPADES,
    EIGHT_OF_CLUBS,
    FIVE_OF_CLUBS,
    FIVE_OF_DIAMONDS,
    FIVE_OF_HEARTS,
    FIVE_OF_SPADES,
    FOUR_OF_HEARTS,
    JACK_OF_CLUBS,
    KING_OF_HEARTS,
    KING_OF_SPADES,
    NINE_OF_HEARTS,
    NINE_OF_SPADES,
    QUEEN_OF_DIAMONDS,
    SEVEN_OF_HEARTS,
    THREE_OF_DIAMONDS,
    TWO_OF_CLUBS,
)
from cardwork.cards.joker import Joker
from cardwork.rounds.seating import rotation

from ..cases import Case, descriptions
from .driving import FIRST_CARD, SEATS, commit_the_turn, held_by, revealed

SECOND_TURN: Final[int] = 2
NO_CARDS: Final[int] = 0
ONE_TRANSACTION: Final[int] = 1
FIRST_TRANSACTION: Final[int] = 0
BLACK_JOKER: Final[Joker] = Joker(red=False)


@dataclass(frozen=True)
class TurnCase(Case):
    revealed: Cards
    winner: int
    taken: int


TURNS: Final[tuple[TurnCase, ...]] = (
    TurnCase(
        description="the highest rank takes the turn",
        revealed=(SEVEN_OF_HEARTS, KING_OF_SPADES, THREE_OF_DIAMONDS),
        winner=1,
        taken=10,
    ),
    TurnCase(
        description="a tie of rank falls to the stronger suit",
        revealed=(NINE_OF_HEARTS, NINE_OF_SPADES),
        winner=1,
        taken=9,
    ),
    TurnCase(
        description="spades stand above hearts, hearts above diamonds, diamonds above clubs",
        revealed=(FIVE_OF_CLUBS, FIVE_OF_DIAMONDS, FIVE_OF_HEARTS, FIVE_OF_SPADES),
        winner=3,
        taken=15,
    ),
    TurnCase(
        description="pips count at their face value",
        revealed=(TWO_OF_CLUBS, FOUR_OF_HEARTS, EIGHT_OF_CLUBS),
        winner=2,
        taken=6,
    ),
    TurnCase(
        description="jack through ace count ten each",
        revealed=(JACK_OF_CLUBS, QUEEN_OF_DIAMONDS, KING_OF_HEARTS, ACE_OF_SPADES),
        winner=3,
        taken=30,
    ),
    TurnCase(
        description="an ace stands above a king",
        revealed=(ACE_OF_CLUBS, KING_OF_SPADES),
        winner=0,
        taken=10,
    ),
    TurnCase(
        description="the card taking the turn adds nothing of its own",
        revealed=(ACE_OF_SPADES, TWO_OF_CLUBS),
        winner=0,
        taken=2,
    ),
)


@pytest.mark.parametrize("case", TURNS, ids=descriptions(TURNS))
def test_the_strongest_card_revealed_takes_what_every_other_one_is_worth(case: TurnCase) -> None:
    assert taken_by(case.revealed) == case.winner
    assert turn_points(case.revealed, case.winner) == case.taken


def test_a_joker_is_no_card_of_this_game() -> None:
    with pytest.raises(ValueError, match="suited cards alone"):
        suited(BLACK_JOKER)


def test_a_turn_nothing_was_revealed_in_has_nobody_to_take_it() -> None:
    with pytest.raises(ValueError, match="strongest of the cards revealed"):
        taken_by(())


def test_the_cards_turn_over_face_up_on_the_discard_from_the_leader_round_the_table(showdown: ShowdownGame) -> None:
    order = rotation(showdown.state.led_by, SEATS)
    committed = {seat: held_by(showdown, seat)[FIRST_CARD] for seat in range(SEATS)}

    commit_the_turn(showdown, Holding.HAND)

    assert revealed(showdown) == tuple(committed[seat] for seat in order)
    assert all(not game_card.face_down for game_card in showdown.board.zone(DISCARD).cards)
    assert all(len(showdown.board.zone(tray_of(seat)).cards) == NO_CARDS for seat in range(SEATS))


def test_the_turn_scores_its_points_to_the_seat_whose_card_was_strongest(showdown: ShowdownGame) -> None:
    order = rotation(showdown.state.led_by, SEATS)
    shown = tuple(held_by(showdown, seat)[FIRST_CARD] for seat in order)
    strongest = taken_by(shown)

    commit_the_turn(showdown, Holding.HAND)

    assert showdown.state.round_points == awarded(
        (NOTHING,) * SEATS,
        order[strongest],
        turn_points(shown, strongest),
    )
    assert showdown.state.points == (NOTHING,) * SEATS
    assert showdown.state.turn_number == SECOND_TURN
    assert showdown.state.to_act == frozenset(range(SEATS))


def test_the_reveal_the_points_and_the_next_turn_land_in_one_transaction(showdown: ShowdownGame) -> None:
    settled = commit_the_turn(showdown, Holding.HAND)

    assert len(settled) == ONE_TRANSACTION
    assert settled[FIRST_TRANSACTION].move is None
    assert tuple(effect.kind for effect in settled[FIRST_TRANSACTION].effects) == ("move_cards",) * SEATS + (
        "set_state",
    )
