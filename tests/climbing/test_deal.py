from dataclasses import dataclass
from random import Random
from typing import Final

import pytest

from cardgames.backend.climbing.game import ClimbingGame
from cardgames.backend.climbing.rules import CLIMBING_RANKING, SEATS_LEAST, SEATS_MOST
from cardgames.backend.climbing.state import ClimbingPhase, ClimbingState
from cardwork.decks.standard import standard_deck, standard_decks
from cardwork.effects.effects import Effects
from cardwork.exceptions import GameValidationError
from cardwork.moves.actions import Play
from cardwork.positions.position import Position
from cardwork.rounds.conclusion import Conclusion
from cardwork.rounds.redeal import Redeal
from cardwork.rounds.seating import rotation
from cardwork.states.state import NOTHING
from cardwork.zones.zones import DISCARD, HANDS, STACK
from tests.cases import Case, descriptions

from .driving import (
    DECK,
    FOUR_SEATS,
    FULL_TABLE,
    ROUNDS,
    SEATS,
    SEED,
    TWO_SEATS,
    a_match,
    held_by,
    play_from,
    seat_on_turn,
)

FIRST_ROUND: Final[int] = 1
TOO_MANY_SEATS: Final[int] = 6
TOO_FEW_SEATS: Final[int] = 1
NO_CARDS: Final[int] = 0
ONE_SHARE_SHORT: Final[int] = 1
READER: Final[int] = 0
ANOTHER_SEAT: Final[int] = 1
A_SINGLE: Final[frozenset[int]] = frozenset({0})


class ShortDealGame(ClimbingGame):
    """A game whose deal leaves every seat a card short of the share the deck divides into."""

    def deal_round(
        self,
        position: Position[ClimbingState],
        leader: int,
        rng: Random,
    ) -> Effects[ClimbingState]:
        counts = {
            **HANDS.dealt(self._hand_size - ONE_SHARE_SHORT, rotation(leader, position.players)),
            DISCARD: self._rejected_cards,
        }
        return Redeal(position, pile=STACK, face_down=True).effects(counts, rng)


class GatheringDealGame(ClimbingGame):
    """A game whose deal keeps the cards its shares leave over, setting none of them aside."""

    def deal_round(
        self,
        position: Position[ClimbingState],
        leader: int,
        rng: Random,
    ) -> Effects[ClimbingState]:
        counts = HANDS.dealt(self._hand_size, rotation(leader, position.players))
        return Redeal(position, pile=STACK, face_down=True).effects(counts, rng)


@dataclass(frozen=True)
class DealCase(Case):
    players: int
    each: int
    aside: int


DEALS: Final[tuple[DealCase, ...]] = (
    DealCase(description="two seats halving the deck", players=TWO_SEATS, each=26, aside=NO_CARDS),
    DealCase(description="three seats, a card over", players=SEATS, each=17, aside=1),
    DealCase(description="four seats, the deck divided", players=FOUR_SEATS, each=13, aside=NO_CARDS),
    DealCase(description="five seats, two cards over", players=FULL_TABLE, each=10, aside=2),
)


@pytest.mark.parametrize("case", DEALS, ids=descriptions(DEALS))
def test_a_round_deals_an_equal_share_to_every_seat_and_sets_what_they_leave_over_aside(case: DealCase) -> None:
    game = a_match(case.players, ROUNDS, SEED)

    assert all(len(held_by(game, seat)) == case.each for seat in range(case.players))
    assert game.board.count(DISCARD) == case.aside
    assert game.board.count(STACK) == NO_CARDS
    assert game.state.phase == ClimbingPhase.LEAD
    assert game.state.to_act == frozenset({game.state.led_by})
    assert game.state.round_number == FIRST_ROUND
    assert game.state.rounds == ROUNDS
    assert game.state.points == (NOTHING,) * case.players
    assert game.state.round_points == (NOTHING,) * case.players
    assert game.state.on_table is None
    assert game.state.passed == frozenset()
    assert game.state.winner is None
    game.board.validate_board()


def test_the_deal_of_the_first_round_and_the_cursor_it_opens_land_in_one_transaction(climbing: ClimbingGame) -> None:
    """Three seats leave a card over, so the deal moves cards to each of them and to the pile it lies aside on."""
    opening = climbing.journal.transactions[0]

    assert opening.seq == 0
    assert opening.move is None
    assert tuple(effect.kind for effect in opening.effects) == (
        ("reorder",) + ("move_cards",) * (SEATS + 1) + ("set_state",)
    )


def test_a_table_opens_offering_the_seat_on_lead_every_combination_its_hand_holds(climbing: ClimbingGame) -> None:
    leader = climbing.state.led_by
    moves = climbing.legal_moves(climbing.position)

    assert all(move.player == leader for move in moves)
    assert all(isinstance(move.action, Play) for move in moves)
    assert tuple(move.action.indices for move in moves if isinstance(move.action, Play)) == CLIMBING_RANKING.selections(
        held_by(climbing, leader)
    )


def test_a_hand_lies_face_down_and_the_cards_set_aside_with_it(climbing: ClimbingGame) -> None:
    hands = tuple(climbing.board.zone(HANDS.of(seat)) for seat in range(SEATS))

    assert all(game_card.face_down for hand in hands for game_card in hand.cards)
    assert all(game_card.face_down for game_card in climbing.board.zone(DISCARD).cards)


def test_a_seat_reads_its_own_hand_and_the_size_of_every_other(climbing: ClimbingGame) -> None:
    view = climbing.view(observer=READER)

    assert view.zones[HANDS.of(READER)].cards == climbing.board.zone(HANDS.of(READER)).cards
    assert all(card is None for card in view.zones[HANDS.of(ANOTHER_SEAT)].cards)
    assert len(view.zones[HANDS.of(ANOTHER_SEAT)].cards) == len(held_by(climbing, ANOTHER_SEAT))


def test_a_spectator_reads_the_combination_played_and_the_size_of_everything_else(climbing: ClimbingGame) -> None:
    played = held_by(climbing, seat_on_turn(climbing))[0]
    play_from(climbing, A_SINGLE)

    view = climbing.view(observer=None)

    assert all(card is None for seat in range(SEATS) for card in view.zones[HANDS.of(seat)].cards)
    assert all(card is None for card in view.zones[DISCARD].cards)
    assert view.zones[STACK].cards == climbing.board.zone(STACK).cards
    assert climbing.board.cards(STACK) == (played,)


def test_a_table_seats_two_to_five_players() -> None:
    with pytest.raises(GameValidationError, match=f"seats {SEATS_LEAST} to {SEATS_MOST}"):
        a_match(TOO_MANY_SEATS, ROUNDS, SEED)

    with pytest.raises(GameValidationError, match=f"seats {SEATS_LEAST} to {SEATS_MOST}"):
        a_match(TOO_FEW_SEATS, ROUNDS, SEED)


def test_a_deck_other_than_one_standard_deck_is_refused() -> None:
    with pytest.raises(GameValidationError, match="one standard deck"):
        ClimbingGame(players=SEATS, deck=DECK[:-1], conclusion=Conclusion(rounds=ROUNDS), rng=Random(SEED))

    with pytest.raises(GameValidationError, match="one standard deck"):
        ClimbingGame(
            players=SEATS,
            deck=standard_decks(2, black_jokers=0, red_jokers=0),
            conclusion=Conclusion(rounds=ROUNDS),
            rng=Random(SEED),
        )


def test_a_deck_holding_a_joker_is_refused() -> None:
    with pytest.raises(GameValidationError, match="one standard deck"):
        ClimbingGame(
            players=SEATS,
            deck=standard_deck(black_jokers=1, red_jokers=0),
            conclusion=Conclusion(rounds=ROUNDS),
            rng=Random(SEED),
        )


def test_a_deal_leaving_a_seat_short_of_its_share_is_refused() -> None:
    with pytest.raises(GameValidationError, match="hold a hand of a size other than"):
        ShortDealGame(players=SEATS, deck=DECK, conclusion=Conclusion(rounds=ROUNDS), rng=Random(SEED))


def test_a_deal_keeping_the_cards_the_shares_leave_over_is_refused() -> None:
    with pytest.raises(GameValidationError, match="set 0 cards aside, and equal shares of this deck leave 2"):
        GatheringDealGame(players=FULL_TABLE, deck=DECK, conclusion=Conclusion(rounds=ROUNDS), rng=Random(SEED))
