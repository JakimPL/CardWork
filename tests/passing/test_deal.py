from dataclasses import dataclass
from random import Random
from typing import Final

import pytest

from cardgames.backend.passing.rules import HAND_ON_TURN, HAND_SIZE
from cardgames.backend.passing.state import PassingPhase, PassingState
from cardgames.backend.passing.zones import PILE
from cardwork.decks.standard import standard_decks
from cardwork.effects.effects import Effects
from cardwork.positions.position import Position
from cardwork.rounds.conclusion import Conclusion
from cardwork.rounds.game import NOTHING
from cardwork.rounds.redeal import Redeal
from cardwork.rounds.seating import rotation
from cardwork.zones.zone import hand_of
from cardwork.zones.zones import STACK
from tests.cases import Case, descriptions

from .driving import (
    FIRST_CARD,
    JOKERED_DECK,
    PLAIN_DECK,
    SEATS,
    SEED,
    TWO_SEATS,
    WINNING_LEAD,
    PassingGame,
    a_match,
    exchange,
)

FIRST_ROUND: Final[int] = 1
TOO_MANY_SEATS: Final[int] = 9
TOO_FEW_SEATS: Final[int] = 1
NO_CARDS: Final[int] = 0
ONE_STACKED: Final[int] = 1
READER: Final[int] = 0
ANOTHER_SEAT: Final[int] = 1


class ShortDealGame(PassingGame):
    """A game whose deal gives every seat three cards, leaving the seat leading the round without its fourth."""

    def deal_round(
        self,
        position: Position[PassingState],
        leader: int,
        rng: Random,
    ) -> Effects[PassingState]:
        counts = {hand_of(seat): HAND_SIZE for seat in rotation(leader, position.players)}
        return Redeal(position, pile=PILE, face_down=True).effects(counts, rng)


@dataclass(frozen=True)
class DealCase(Case):
    players: int
    decks: int
    black_jokers: int
    red_jokers: int
    led: int
    each: int
    piled: int
    stacked: int


DEALS: Final[tuple[DealCase, ...]] = (
    DealCase(
        description="two seats over one deck",
        players=2,
        decks=1,
        black_jokers=0,
        red_jokers=0,
        led=HAND_ON_TURN,
        each=HAND_SIZE,
        piled=45,
        stacked=NO_CARDS,
    ),
    DealCase(
        description="eight seats over one deck",
        players=8,
        decks=1,
        black_jokers=0,
        red_jokers=0,
        led=HAND_ON_TURN,
        each=HAND_SIZE,
        piled=27,
        stacked=NO_CARDS,
    ),
    DealCase(
        description="two seats over two decks and two jokers",
        players=2,
        decks=2,
        black_jokers=1,
        red_jokers=1,
        led=HAND_ON_TURN,
        each=HAND_SIZE,
        piled=99,
        stacked=NO_CARDS,
    ),
    DealCase(
        description="eight seats over two decks and four jokers",
        players=8,
        decks=2,
        black_jokers=2,
        red_jokers=2,
        led=HAND_ON_TURN,
        each=HAND_SIZE,
        piled=83,
        stacked=NO_CARDS,
    ),
)


@pytest.mark.parametrize("case", DEALS, ids=descriptions(DEALS))
def test_a_round_deals_three_to_every_seat_and_a_fourth_to_the_one_leading_it(case: DealCase) -> None:
    deck = standard_decks(case.decks, black_jokers=case.black_jokers, red_jokers=case.red_jokers)

    game = a_match(case.players, deck, SEED)
    leader = game.state.led_by

    assert len(game.board.zone(hand_of(leader)).cards) == case.led
    assert all(len(game.board.zone(hand_of(seat)).cards) == case.each for seat in range(case.players) if seat != leader)
    assert len(game.board.zone(PILE).cards) == case.piled
    assert len(game.board.zone(STACK).cards) == case.stacked
    assert game.state.phase == PassingPhase.PASSING
    assert game.state.to_act == frozenset({leader})
    assert game.state.round_number == FIRST_ROUND
    assert game.state.points == (NOTHING,) * case.players
    assert game.state.round_points == (NOTHING,) * case.players
    assert game.state.swapped is False
    assert game.state.winner is None
    game.board.validate_board()


def test_the_deal_of_the_first_round_and_the_cursor_it_opens_land_in_one_transaction(passing: PassingGame) -> None:
    opening = passing.journal.transactions[0]

    assert opening.seq == 0
    assert opening.move is None
    assert tuple(effect.kind for effect in opening.effects) == ("reorder",) + ("move_cards",) * SEATS + ("set_state",)


def test_a_hand_lies_face_down_and_the_pile_with_it(passing: PassingGame) -> None:
    hands = tuple(passing.board.zone(hand_of(seat)) for seat in range(SEATS))

    assert all(game_card.face_down for hand in hands for game_card in hand.cards)
    assert all(game_card.face_down for game_card in passing.board.zone(PILE).cards)


def test_a_seat_reads_its_own_hand_and_the_size_of_every_other(passing: PassingGame) -> None:
    view = passing.view(observer=READER)

    assert view.zones[hand_of(READER)].cards == passing.board.zone(hand_of(READER)).cards
    assert all(card is None for card in view.zones[hand_of(ANOTHER_SEAT)].cards)
    assert len(view.zones[hand_of(ANOTHER_SEAT)].cards) == len(passing.board.zone(hand_of(ANOTHER_SEAT)).cards)
    assert all(card is None for card in view.zones[PILE].cards)
    assert len(view.zones[PILE].cards) == len(passing.board.zone(PILE).cards)


def test_a_spectator_reads_the_stack_and_the_size_of_everything_else(passing: PassingGame) -> None:
    exchange(passing, FIRST_CARD)

    view = passing.view(observer=None)

    assert all(card is None for seat in range(SEATS) for card in view.zones[hand_of(seat)].cards)
    assert all(card is None for card in view.zones[PILE].cards)
    assert view.zones[STACK].cards == passing.board.zone(STACK).cards
    assert len(view.zones[STACK].cards) == ONE_STACKED


def test_a_table_seats_two_to_eight_players() -> None:
    with pytest.raises(ValueError, match=f"seats {TWO_SEATS} to 8"):
        a_match(TOO_MANY_SEATS, PLAIN_DECK, SEED)

    with pytest.raises(ValueError, match=f"seats {TWO_SEATS} to 8"):
        a_match(TOO_FEW_SEATS, PLAIN_DECK, SEED)


def test_a_deck_short_of_a_whole_standard_deck_is_refused() -> None:
    with pytest.raises(ValueError, match="whole standard decks"):
        a_match(SEATS, PLAIN_DECK[:-1], SEED)


def test_a_deck_of_jokers_alone_is_refused() -> None:
    with pytest.raises(ValueError, match="whole standard decks"):
        a_match(SEATS, JOKERED_DECK[len(PLAIN_DECK) :], SEED)


def test_a_deal_leaving_the_leader_without_its_fourth_card_is_refused() -> None:
    with pytest.raises(ValueError, match="hold a hand of a size other than"):
        ShortDealGame(players=SEATS, deck=PLAIN_DECK, conclusion=Conclusion(lead=WINNING_LEAD), rng=Random(SEED))
