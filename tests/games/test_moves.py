from random import Random
from typing import Final

from cardwork.moves.actions import Play
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.states.state import GameState

from .conftest import SEED
from .demo import DECK, HAND_SIZE, SEATS, BareGame, DiscardGame

FIRST_SEAT: Final[int] = 0
LAST_SEAT: Final[int] = SEATS - 1
NO_MOVES: Final[Moves] = ()


class DeclaringGame(DiscardGame):
    """A game whose move list is not read seat by seat, which states the whole of it for itself."""

    def legal_moves(self, position: Position[GameState]) -> Moves:
        return (Move(player=LAST_SEAT, action=Play(group="discard", indices=frozenset({0}))),)


def test_a_game_listing_no_move_offers_none() -> None:
    game = BareGame(players=SEATS, deck=DECK, rng=Random(SEED))

    assert game.moves_of(game.position, FIRST_SEAT) == NO_MOVES
    assert game.legal_moves(game.position) == NO_MOVES


def test_a_seat_is_offered_one_move_for_every_card_it_holds(game: DiscardGame) -> None:
    assert len(game.moves_of(game.position, FIRST_SEAT)) == HAND_SIZE


def test_the_moves_a_game_states_of_one_seat_are_the_ones_that_seat_is_offered(game: DiscardGame) -> None:
    offered = game.legal_moves(game.position)

    assert [move for move in offered if move.player == FIRST_SEAT] == list(game.moves_of(game.position, FIRST_SEAT))


def test_the_move_list_gathers_the_seats_that_owe_an_action_in_seat_order(game: DiscardGame) -> None:
    offered = game.legal_moves(game.position)

    assert [move.player for move in offered] == [seat for seat in range(SEATS) for _ in range(HAND_SIZE)]


def test_a_seat_owing_no_action_is_offered_nothing_it_holds_cards_for(game: DiscardGame) -> None:
    acted = game.step(game.position, game.legal_moves(game.position)[0], Random(SEED))

    assert game.moves_of(acted, FIRST_SEAT)
    assert not [move for move in game.legal_moves(acted) if move.player == FIRST_SEAT]


def test_a_game_stating_its_whole_move_list_is_read_as_it_states_it() -> None:
    game = DeclaringGame(players=SEATS, deck=DECK, rng=Random(SEED))

    assert [move.player for move in game.legal_moves(game.position)] == [LAST_SEAT]
