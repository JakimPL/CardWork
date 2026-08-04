from dataclasses import dataclass
from random import Random
from typing import Final

import pytest

from cardgames.backend.showdown.game import ONE_ROUND, ShowdownGame
from cardgames.backend.showdown.rules import (
    BLIND_SIZE,
    FIRST_TURN,
    HAND_SIZE,
    NOTHING,
    ONE_CARD,
)
from cardgames.backend.showdown.state import ShowdownPhase, ShowdownState
from cardgames.backend.showdown.zones import DISCARD, STOCK, blind_of, hand_of, tray_of
from cardwork.decks.decks import jokers
from cardwork.decks.standard import standard_deck
from cardwork.effects.effects import Effects
from cardwork.positions.position import Position
from cardwork.rounds.redeal import Redeal
from cardwork.rounds.seating import rotation
from tests.cases import Case, descriptions

from .driving import DECK, FULL_TABLE, ROUNDS, SEATS, SEED, TWO_SEATS, a_match

FIRST_ROUND: Final[int] = 1
NO_ROUNDS: Final[int] = 0
TOO_MANY_SEATS: Final[int] = 6
TOO_FEW_SEATS: Final[int] = 1
NO_CARDS: Final[int] = 0
DEALT_ZONES_PER_SEAT: Final[int] = 2
READER: Final[int] = 0
ANOTHER_SEAT: Final[int] = 1


class ShortDealGame(ShowdownGame):
    """A game whose deal leaves every seat one card short of the five it reads."""

    def deal_round(
        self,
        position: Position[ShowdownState],
        leader: int,
        rng: Random,
    ) -> Effects[ShowdownState]:
        counts = {
            zone: count
            for seat in rotation(leader, position.players)
            for zone, count in ((hand_of(seat), HAND_SIZE - ONE_CARD), (blind_of(seat), BLIND_SIZE))
        }
        return Redeal(position, pile=STOCK, face_down=True).effects(counts, rng)


@dataclass(frozen=True)
class DealCase(Case):
    players: int
    rounds: int
    read: int
    blind: int
    stocked: int


DEALS: Final[tuple[DealCase, ...]] = (
    DealCase(description="two seats", players=2, rounds=ONE_ROUND, read=HAND_SIZE, blind=BLIND_SIZE, stocked=32),
    DealCase(description="three seats", players=3, rounds=ROUNDS, read=HAND_SIZE, blind=BLIND_SIZE, stocked=22),
    DealCase(description="four seats", players=4, rounds=ROUNDS, read=HAND_SIZE, blind=BLIND_SIZE, stocked=12),
    DealCase(description="five seats", players=5, rounds=ROUNDS, read=HAND_SIZE, blind=BLIND_SIZE, stocked=2),
)


@pytest.mark.parametrize("case", DEALS, ids=descriptions(DEALS))
def test_a_round_deals_every_seat_five_cards_to_read_and_five_it_may_not(case: DealCase) -> None:
    game = a_match(case.players, case.rounds, SEED)

    assert all(len(game.board.zone(hand_of(seat)).cards) == case.read for seat in range(case.players))
    assert all(len(game.board.zone(blind_of(seat)).cards) == case.blind for seat in range(case.players))
    assert all(len(game.board.zone(tray_of(seat)).cards) == NO_CARDS for seat in range(case.players))
    assert len(game.board.zone(STOCK).cards) == case.stocked
    assert len(game.board.zone(DISCARD).cards) == NO_CARDS
    assert game.state.phase == ShowdownPhase.COMMITTING
    assert game.state.to_act == frozenset(range(case.players))
    assert game.state.round_number == FIRST_ROUND
    assert game.state.turn_number == FIRST_TURN
    assert game.state.rounds == case.rounds
    assert game.state.points == (NOTHING,) * case.players
    assert game.state.round_points == (NOTHING,) * case.players
    game.board.validate_board()


def test_the_deal_of_the_first_round_and_the_cursor_it_opens_land_in_one_transaction(showdown: ShowdownGame) -> None:
    opening = showdown.journal.transactions[0]

    assert opening.seq == 0
    assert opening.move is None
    assert tuple(effect.kind for effect in opening.effects) == (
        ("reorder",) + ("move_cards",) * (SEATS * DEALT_ZONES_PER_SEAT) + ("set_state",)
    )


def test_every_card_dealt_and_every_card_left_in_the_stock_lies_face_down(showdown: ShowdownGame) -> None:
    dealt = tuple(
        game_card
        for seat in range(SEATS)
        for zone in (hand_of(seat), blind_of(seat))
        for game_card in showdown.board.zone(zone).cards
    )

    assert all(game_card.face_down for game_card in dealt)
    assert all(game_card.face_down for game_card in showdown.board.zone(STOCK).cards)


def test_a_seat_reads_its_own_hand_and_the_size_of_every_other_holding(showdown: ShowdownGame) -> None:
    view = showdown.view(observer=READER)

    assert view.zones[hand_of(READER)].cards == showdown.board.zone(hand_of(READER)).cards
    assert all(card is None for card in view.zones[hand_of(ANOTHER_SEAT)].cards)
    assert len(view.zones[hand_of(ANOTHER_SEAT)].cards) == HAND_SIZE
    assert all(card is None for card in view.zones[blind_of(ANOTHER_SEAT)].cards)
    assert len(view.zones[blind_of(ANOTHER_SEAT)].cards) == BLIND_SIZE
    assert all(card is None for card in view.zones[STOCK].cards)
    assert len(view.zones[STOCK].cards) == len(showdown.board.zone(STOCK).cards)


def test_a_spectator_reads_the_size_of_every_zone_and_the_cards_of_none(showdown: ShowdownGame) -> None:
    view = showdown.view(observer=None)

    assert all(card is None for zone in view.zones.values() for card in zone.cards)
    assert {zone_id: len(zone.cards) for zone_id, zone in view.zones.items()} == {
        zone_id: len(zone.cards) for zone_id, zone in showdown.board.zones.items()
    }


def test_a_table_seats_two_to_five_players() -> None:
    with pytest.raises(ValueError, match=f"seats {TWO_SEATS} to {FULL_TABLE}"):
        a_match(TOO_MANY_SEATS, ROUNDS, SEED)

    with pytest.raises(ValueError, match=f"seats {TWO_SEATS} to {FULL_TABLE}"):
        a_match(TOO_FEW_SEATS, ROUNDS, SEED)


def test_a_match_runs_at_least_one_round() -> None:
    with pytest.raises(ValueError, match=f"at least {ONE_ROUND} round"):
        a_match(SEATS, NO_ROUNDS, SEED)


def test_a_deck_short_of_a_standard_one_is_refused() -> None:
    with pytest.raises(ValueError, match="one standard deck"):
        ShowdownGame(players=SEATS, deck=DECK[:-1], rounds=ROUNDS, rng=Random(SEED))


def test_a_deck_carrying_jokers_is_refused() -> None:
    with pytest.raises(ValueError, match="one standard deck"):
        ShowdownGame(
            players=SEATS,
            deck=standard_deck() + jokers(black=1, red=1),
            rounds=ROUNDS,
            rng=Random(SEED),
        )


def test_a_deal_leaving_a_seat_short_of_the_five_it_reads_is_refused() -> None:
    with pytest.raises(ValueError, match=f"other than {HAND_SIZE} cards to read"):
        ShortDealGame(players=SEATS, deck=DECK, rounds=ROUNDS, rng=Random(SEED))
