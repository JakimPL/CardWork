from dataclasses import dataclass
from random import Random
from typing import Final

import pytest

from cardgames.backend.climbing.game import ClimbingGame
from cardgames.backend.climbing.rules import (
    CLIMBING_RANKING,
    DECKS_SPOKEN,
    HAND_MOST,
    OPENING_CARD,
    SEATS_LEAST,
    SEATS_MOST,
)
from cardgames.backend.climbing.state import ClimbingPhase, ClimbingState
from cardwork.cards.game import CardOrJoker, CardsOrJokers
from cardwork.decks.decks import named
from cardwork.decks.standard import standard_deck, standard_decks
from cardwork.effects.effects import Effects
from cardwork.exceptions import GameValidationError, IllegalMove
from cardwork.moves.actions import Play
from cardwork.moves.move import Move
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
    TWO_DECK,
    TWO_SEATS,
    a_match,
    a_two_deck_match,
    held_by,
    places_of,
    play_from,
    seat_on_turn,
)

FIRST_ROUND: Final[int] = 1
TOO_MANY_SEATS: Final[int] = 6
TOO_FEW_SEATS: Final[int] = 1
THREE_DECKS: Final[int] = 3
TWO_COPIES: Final[int] = 2

# The one deal of two decks these read, where the seat the cards went out from is not the lowest holding the
# opening card, so the seat that opens tells the reading from the leader apart from a walk in seat order.
DOUBLED_SEED: Final[int] = 4
DOUBLED_LEADER: Final[int] = 1
NO_CARDS: Final[int] = 0
ONE_SHARE_SHORT: Final[int] = 1
READER: Final[int] = 0
ANOTHER_SEAT: Final[int] = 1


def _held_twice(hand: CardsOrJokers) -> tuple[tuple[int, ...], CardOrJoker]:
    """The two places one card of a hand stands at, and the card, which two decks in play leave hands holding.

    Raises:
        ValueError: when the hand holds no card of the deck twice.
    """
    for place, card in enumerate(hand):
        doubled = tuple(other for other, held in enumerate(hand) if held == card)
        if len(doubled) == TWO_COPIES:
            return doubled, hand[place]

    raise ValueError(f"A hand of {len(hand)} cards dealt from two decks holds one twice, and this one holds none")


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


class RecordedDealGame(ClimbingGame):
    """A game keeping the seat each deal went out from, which the cursor gives up as the match names its opener.

    `_opened` reads the leader the round was dealt to and then stands the opener in its place, so a test that
    wants to know which rotation the opening card was looked for along reads it here.
    """

    dealt_from: int | None = None

    def deal_round(
        self,
        position: Position[ClimbingState],
        leader: int,
        rng: Random,
    ) -> Effects[ClimbingState]:
        self.dealt_from = leader
        return super().deal_round(position, leader, rng)


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
    assert game.state.phase == ClimbingPhase.OPENING
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


def test_the_seat_a_match_opens_on_is_named_in_the_settlement_after_the_deal(climbing: ClimbingGame) -> None:
    """The cards decide the seat, so the deal lands first and the reading of it lands in its own transaction."""
    choosing = climbing.journal.transactions[1]

    assert choosing.seq == 1
    assert choosing.move is None
    assert tuple(effect.kind for effect in choosing.effects) == ("set_state",)


@pytest.mark.parametrize("case", DEALS, ids=descriptions(DEALS))
def test_the_first_round_deals_the_opening_card_to_a_seat_rather_than_setting_it_aside(case: DealCase) -> None:
    game = a_match(case.players, ROUNDS, SEED)

    assert OPENING_CARD not in game.board.cards(DISCARD)
    assert OPENING_CARD in held_by(game, game.state.led_by)


def test_the_seat_dealt_the_opening_card_is_the_one_the_match_opens_on(climbing: ClimbingGame) -> None:
    holding = tuple(seat for seat in range(SEATS) if OPENING_CARD in held_by(climbing, seat))

    assert holding == (climbing.state.led_by,)
    assert climbing.state.to_act == frozenset({climbing.state.led_by})


def test_a_table_opens_offering_that_seat_every_combination_of_its_hand_holding_the_opening_card(
    climbing: ClimbingGame,
) -> None:
    leader = climbing.state.led_by
    hand = held_by(climbing, leader)
    holding = tuple(places for places in CLIMBING_RANKING.selections(hand) if OPENING_CARD in named(hand, places))
    moves = climbing.legal_moves(climbing.position)

    assert all(move.player == leader for move in moves)
    assert all(isinstance(move.action, Play) for move in moves)
    assert tuple(move.action.indices for move in moves if isinstance(move.action, Play)) == holding
    assert holding != CLIMBING_RANKING.selections(hand)


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
    play_from(climbing, places_of(held_by(climbing, seat_on_turn(climbing)), OPENING_CARD))

    view = climbing.view(observer=None)

    assert all(card is None for seat in range(SEATS) for card in view.zones[HANDS.of(seat)].cards)
    assert all(card is None for card in view.zones[DISCARD].cards)
    assert view.zones[STACK].cards == climbing.board.zone(STACK).cards
    assert climbing.board.cards(STACK) == (OPENING_CARD,)


def test_a_table_seats_two_to_five_players() -> None:
    with pytest.raises(GameValidationError, match=f"seats {SEATS_LEAST} to {SEATS_MOST}"):
        a_match(TOO_MANY_SEATS, ROUNDS, SEED)

    with pytest.raises(GameValidationError, match=f"seats {SEATS_LEAST} to {SEATS_MOST}"):
        a_match(TOO_FEW_SEATS, ROUNDS, SEED)


TWO_DECK_DEALS: Final[tuple[DealCase, ...]] = (
    DealCase(description="four seats, both decks divided", players=FOUR_SEATS, each=26, aside=NO_CARDS),
    DealCase(description="five seats, four cards over", players=FULL_TABLE, each=20, aside=4),
)

TOO_FEW_FOR_TWO_DECKS: Final[tuple[int, ...]] = (TWO_SEATS, SEATS)


@pytest.mark.parametrize("case", TWO_DECK_DEALS, ids=descriptions(TWO_DECK_DEALS))
def test_a_round_over_two_decks_deals_the_share_they_divide_into(case: DealCase) -> None:
    """Twice the cards is twice the hand, which the share a table divides the deck into already follows."""
    game = a_two_deck_match(case.players, ROUNDS, SEED)

    assert all(len(held_by(game, seat)) == case.each for seat in range(case.players))
    assert game.board.count(DISCARD) == case.aside
    assert game.state.phase == ClimbingPhase.OPENING
    assert game.state.to_act == frozenset({game.state.led_by})
    game.board.validate_board()


def test_a_match_over_two_decks_opens_on_the_first_seat_from_the_leader_holding_the_opening_card() -> None:
    """Two decks hold the opening card twice, so which of the seats holding one opens is read the way it was dealt."""
    game = RecordedDealGame(
        players=FOUR_SEATS,
        deck=TWO_DECK,
        conclusion=Conclusion(rounds=ROUNDS),
        rng=Random(DOUBLED_SEED),
    )
    holding = tuple(seat for seat in rotation(DOUBLED_LEADER, game.players) if OPENING_CARD in held_by(game, seat))

    assert game.dealt_from == DOUBLED_LEADER
    assert len(holding) == TWO_COPIES
    assert holding[0] != min(holding)
    assert game.state.led_by == holding[0]
    assert game.state.to_act == frozenset({holding[0]})


def test_a_match_over_one_deck_opens_on_the_one_seat_holding_the_opening_card() -> None:
    """One copy stands at one seat, which every rotation round the table reaches at the same one."""
    game = a_match(FOUR_SEATS, ROUNDS, SEED)
    holding = tuple(seat for seat in range(game.players) if OPENING_CARD in held_by(game, seat))

    assert holding == (game.state.led_by,)


@pytest.mark.parametrize("players", TOO_FEW_FOR_TWO_DECKS)
def test_a_table_too_small_to_share_two_decks_into_hands_this_game_reads_is_refused(players: int) -> None:
    """The one thing the seats and the decks state together, which is why the hand is where they are held.

    What a seat answering a combination is offered is every combination of as many cards its hand holds, and
    that reading grows with the hand far faster than the hand does — so a hand beyond the largest this game
    deals is refused where the seating and the deck are, rather than met as a turn nobody waits out.
    """
    with pytest.raises(GameValidationError, match=f"runs to {HAND_MOST} cards"):
        a_two_deck_match(players, ROUNDS, SEED)


def test_two_copies_of_one_card_read_as_the_one_card_and_make_no_pair() -> None:
    """What `Duplicates.COLLAPSE` comes to at the table: the doubling adds cards and adds no combination.

    So the contest over two decks is the contest over one, played with twice the hand: a pair asks for two ranks
    that read apart, and a card held twice answers one of the two demands it fills.
    """
    game = a_two_deck_match(FOUR_SEATS, ROUNDS, SEED)
    opener = game.state.led_by
    hand = held_by(game, opener)
    doubled, card = _held_twice(hand)

    assert len(doubled) == TWO_COPIES
    assert CLIMBING_RANKING.exactly((card, card)) is None
    assert all(places != frozenset(doubled) for places in CLIMBING_RANKING.selections(hand))
    with pytest.raises(IllegalMove, match="combination this game is played by"):
        game.submit(
            Move(player=opener, action=Play(group=HANDS.name, indices=frozenset(doubled))),
            base_seq=game.head,
        )


def test_a_deck_other_than_one_whole_standard_deck_or_two_is_refused() -> None:
    with pytest.raises(GameValidationError, match=DECKS_SPOKEN):
        ClimbingGame(players=SEATS, deck=DECK[:-1], conclusion=Conclusion(rounds=ROUNDS), rng=Random(SEED))

    with pytest.raises(GameValidationError, match=DECKS_SPOKEN):
        ClimbingGame(
            players=SEATS,
            deck=standard_decks(THREE_DECKS),
            conclusion=Conclusion(rounds=ROUNDS),
            rng=Random(SEED),
        )


def test_a_deck_holding_a_joker_is_refused() -> None:
    """A joker names no rank the ranking places, so a card standing in for another is refused with the deck."""
    with pytest.raises(GameValidationError, match=DECKS_SPOKEN):
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
