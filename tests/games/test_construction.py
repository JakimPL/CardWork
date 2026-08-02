from random import Random

import pytest

from cardwork.cards.joker import Joker
from cardwork.decks.draw import permutation
from cardwork.effects.effects import Reorder
from cardwork.positions.position import Position
from cardwork.states.state import GameState

from .conftest import SEED
from .demo import DECK, HAND_SIZE, SEATS, BareGame, DiscardGame, ShortDealGame, hand_of


class WatchfulGame(DiscardGame):
    """A game that keeps the position it was handed for its final check, so a test may read it."""

    checked: Position[GameState]

    def _final_validation(self, position: Position[GameState]) -> None:
        self.checked = position
        super()._final_validation(position)


class MisscoredGame(DiscardGame):
    """A game opening with a points table sized for a table other than its own."""

    def _initialize(self, players: int) -> GameState:
        return GameState(phase="deal", points=(0,))


def test_construction_commits_the_deal_as_one_transaction(game: DiscardGame) -> None:
    assert game.head == 1


def test_the_deal_carries_no_move(game: DiscardGame) -> None:
    assert game.journal.transactions[0].move is None


def test_construction_opens_the_round_for_every_seat(game: DiscardGame) -> None:
    assert game.state.phase == "play"
    assert game.state.to_act == frozenset(range(SEATS))


def test_the_table_reports_the_seats_it_was_built_for(game: DiscardGame) -> None:
    assert game.players == SEATS == game.position.players


def test_construction_deals_every_seat_a_hand(game: DiscardGame) -> None:
    assert all(len(game.board.zone(hand_of(seat)).cards) == HAND_SIZE for seat in range(SEATS))


def test_the_origin_snapshot_predates_the_deal(game: DiscardGame) -> None:
    origin = game.snapshot(0)

    assert all(origin.board.zone(hand_of(seat)).cards == () for seat in range(SEATS))
    assert origin.state.phase == "deal"


def test_the_journal_keeps_the_origin_the_table_started_from(game: DiscardGame) -> None:
    assert game.journal.initial == game.snapshot(0)


def test_the_final_check_reads_the_dealt_position() -> None:
    game = WatchfulGame(players=SEATS, deck=DECK, rng=Random(SEED))

    assert len(game.checked.board.zone(hand_of(0)).cards) == HAND_SIZE


def test_construction_counts_the_cards_of_a_game_that_scores_nothing_yet() -> None:
    with pytest.raises(ValueError):
        ShortDealGame(players=SEATS, deck=DECK, rng=Random(SEED))


def test_construction_matches_the_points_table_to_the_table() -> None:
    with pytest.raises(ValueError):
        MisscoredGame(players=SEATS, deck=DECK, rng=Random(SEED))


@pytest.mark.parametrize(
    ("players", "deck"),
    [
        pytest.param(0, DECK, id="a table with no seats"),
        pytest.param(SEATS, (), id="an empty deck"),
    ],
)
def test_construction_rejects_a_table_the_engine_cannot_seat(players: int, deck: tuple[object, ...]) -> None:
    with pytest.raises(ValueError):
        DiscardGame(players=players, deck=deck, rng=Random(SEED))


def test_construction_puts_the_game_s_own_seating_rule_to_the_table() -> None:
    with pytest.raises(ValueError):
        DiscardGame(players=1, deck=DECK, rng=Random(SEED))


def test_construction_puts_the_game_s_own_deck_rule_to_the_deck() -> None:
    with pytest.raises(ValueError):
        DiscardGame(players=SEATS, deck=DECK + (Joker(red=True),), rng=Random(SEED))


def test_the_deal_records_the_shuffle_it_drew(game: DiscardGame) -> None:
    shuffle = game.journal.transactions[0].effects[0]

    assert isinstance(shuffle, Reorder)
    assert shuffle.order == permutation(len(DECK), Random(SEED))


def test_two_tables_drawn_from_the_same_seed_deal_alike() -> None:
    first = DiscardGame(players=SEATS, deck=DECK, rng=Random(SEED))
    second = DiscardGame(players=SEATS, deck=DECK, rng=Random(SEED))

    assert first.position == second.position


def test_a_game_may_open_with_nothing_dealt_at_all() -> None:
    game = BareGame(players=SEATS, deck=DECK, rng=Random(SEED))

    assert game.journal.transactions[0].effects == ()
    assert game.board.zone("draw").cards == game.snapshot(0).board.zone("draw").cards
