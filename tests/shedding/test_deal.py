from dataclasses import dataclass
from random import Random
from typing import Final

import pytest

from cardgames.backend.shedding.game import SheddingGame
from cardgames.backend.shedding.rules import HAND_SIZE, NOTHING, SHED_LEAST
from cardgames.backend.shedding.state import SheddingPhase, SheddingState
from cardgames.backend.shedding.zones import STOCK
from cardwork.decks.standard import standard_deck, standard_decks
from cardwork.effects.effects import Effects
from cardwork.positions.position import Position
from cardwork.rounds.conclusion import Conclusion
from cardwork.rounds.redeal import Redeal
from cardwork.rounds.seating import rotation
from cardwork.zones.zone import hand_of
from cardwork.zones.zones import DISCARD
from tests.cases import Case, descriptions

from .driving import (
    DECK,
    ROUNDS,
    SEATS,
    SEED,
    TWO_SEATS,
    a_match,
    play_to_a_shed,
    stocked,
)

FIRST_ROUND: Final[int] = 1
TOO_MANY_SEATS: Final[int] = 7
TOO_FEW_SEATS: Final[int] = 1
NO_CARDS: Final[int] = 0
READER: Final[int] = 0
ANOTHER_SEAT: Final[int] = 1


class ShortDealGame(SheddingGame):
    """A game whose deal leaves every seat a card short of the hand a round is played from."""

    def deal_round(
        self,
        position: Position[SheddingState],
        leader: int,
        rng: Random,
    ) -> Effects[SheddingState]:
        counts = {hand_of(seat): HAND_SIZE - 1 for seat in rotation(leader, position.players)}
        return Redeal(position, pile=STOCK, face_down=True).effects(counts, rng)


@dataclass(frozen=True)
class DealCase(Case):
    players: int
    each: int
    stocked: int


DEALS: Final[tuple[DealCase, ...]] = (
    DealCase(description="two seats", players=TWO_SEATS, each=HAND_SIZE, stocked=44),
    DealCase(description="three seats", players=SEATS, each=HAND_SIZE, stocked=40),
    DealCase(description="six seats", players=6, each=HAND_SIZE, stocked=28),
)


@pytest.mark.parametrize("case", DEALS, ids=descriptions(DEALS))
def test_a_round_deals_four_cards_to_every_seat_and_leaves_the_rest_in_the_stock(case: DealCase) -> None:
    game = a_match(case.players, ROUNDS, SEED)

    assert all(len(game.board.zone(hand_of(seat)).cards) == case.each for seat in range(case.players))
    assert stocked(game) == case.stocked
    assert len(game.board.zone(DISCARD).cards) == NO_CARDS
    assert game.state.phase == SheddingPhase.SHEDDING
    assert game.state.to_act == frozenset({game.state.led_by})
    assert game.state.round_number == FIRST_ROUND
    assert game.state.rounds == ROUNDS
    assert game.state.points == (NOTHING,) * case.players
    assert game.state.round_points == (NOTHING,) * case.players
    assert game.state.winner is None
    game.board.validate_board()


def test_the_deal_of_the_first_round_and_the_cursor_it_opens_land_in_one_transaction(shedding: SheddingGame) -> None:
    opening = shedding.journal.transactions[0]

    assert opening.seq == 0
    assert opening.move is None
    assert tuple(effect.kind for effect in opening.effects) == ("reorder",) + ("move_cards",) * SEATS + ("set_state",)


def test_a_table_opens_offering_the_seat_leading_the_round_its_turn(shedding: SheddingGame) -> None:
    """A deal leaves the stock holding cards, so the seat it opens on always has its draw to take."""
    assert stocked(shedding) > NO_CARDS
    assert shedding.legal_moves(shedding.position) != ()


def test_a_hand_lies_face_down_and_the_stock_with_it(shedding: SheddingGame) -> None:
    hands = tuple(shedding.board.zone(hand_of(seat)) for seat in range(SEATS))

    assert all(game_card.face_down for hand in hands for game_card in hand.cards)
    assert all(game_card.face_down for game_card in shedding.board.zone(STOCK).cards)


def test_a_seat_reads_its_own_hand_and_the_size_of_every_other(shedding: SheddingGame) -> None:
    view = shedding.view(observer=READER)

    assert view.zones[hand_of(READER)].cards == shedding.board.zone(hand_of(READER)).cards
    assert all(card is None for card in view.zones[hand_of(ANOTHER_SEAT)].cards)
    assert len(view.zones[hand_of(ANOTHER_SEAT)].cards) == HAND_SIZE
    assert all(card is None for card in view.zones[STOCK].cards)
    assert len(view.zones[STOCK].cards) == stocked(shedding)


def test_a_spectator_reads_the_discard_and_the_size_of_everything_else(shedding: SheddingGame) -> None:
    play_to_a_shed(shedding)

    view = shedding.view(observer=None)

    assert all(card is None for seat in range(SEATS) for card in view.zones[hand_of(seat)].cards)
    assert all(card is None for card in view.zones[STOCK].cards)
    assert view.zones[DISCARD].cards == shedding.board.zone(DISCARD).cards
    assert len(view.zones[DISCARD].cards) >= SHED_LEAST


def test_a_table_seats_two_to_six_players() -> None:
    with pytest.raises(ValueError, match=f"seats {TWO_SEATS} to 6"):
        a_match(TOO_MANY_SEATS, ROUNDS, SEED)

    with pytest.raises(ValueError, match=f"seats {TWO_SEATS} to 6"):
        a_match(TOO_FEW_SEATS, ROUNDS, SEED)


def test_a_deck_other_than_one_standard_deck_is_refused() -> None:
    with pytest.raises(ValueError, match="one standard deck"):
        SheddingGame(players=SEATS, deck=DECK[:-1], conclusion=Conclusion(rounds=ROUNDS), rng=Random(SEED))

    with pytest.raises(ValueError, match="one standard deck"):
        SheddingGame(
            players=SEATS, deck=standard_decks(2, black_jokers=0, red_jokers=0), conclusion=Conclusion(rounds=ROUNDS)
        )


def test_a_deck_holding_a_joker_is_refused() -> None:
    with pytest.raises(ValueError, match="one standard deck"):
        SheddingGame(
            players=SEATS,
            deck=standard_deck(black_jokers=1, red_jokers=0),
            conclusion=Conclusion(rounds=ROUNDS),
            rng=Random(SEED),
        )


def test_a_deal_leaving_a_seat_short_of_its_hand_is_refused() -> None:
    with pytest.raises(ValueError, match="hold a hand of a size other than"):
        ShortDealGame(players=SEATS, deck=DECK, conclusion=Conclusion(rounds=ROUNDS), rng=Random(SEED))
