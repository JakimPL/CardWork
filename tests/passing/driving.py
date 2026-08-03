from collections.abc import Callable
from random import Random
from typing import Final

from cardgames.passing.game import PassingGame
from cardgames.passing.state import PassingState
from cardgames.passing.zones import PILE, STACK, hand_of
from cardwork.cards.game import CardsOrJokers
from cardwork.decks.deck import Deck
from cardwork.decks.standard import standard_decks
from cardwork.moves.actions import Give, Take
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.rounds.seating import next_seat
from cardwork.transactions.transaction import Transaction
from cardwork.zones.zone import cards_of

SEATS: Final[int] = 3
TWO_SEATS: Final[int] = 2
SEED: Final[int] = 20260803
FIRST_CARD: Final[int] = 0
ONE_CARD: Final[int] = 1
PLAIN_DECK: Final[Deck] = standard_decks(1, black_jokers=0, red_jokers=0)
JOKERED_DECK: Final[Deck] = standard_decks(1, black_jokers=1, red_jokers=1)

type Chooser = Callable[[Moves], Move]


def a_match(players: int, deck: Deck, seed: int) -> PassingGame:
    """A fresh table of that many seats and that deck, drawing from a generator of that seed."""
    return PassingGame(players=players, deck=deck, rng=Random(seed))


def seat_on_turn(game: PassingGame) -> int:
    """The seat the turn stands with.

    Raises:
        ValueError: when the turn stands with several seats or with none, which a round in play never reaches.
    """
    seat = game.state.current
    if seat is None:
        raise ValueError(f"One seat holds the turn, and it stands with {sorted(game.state.to_act)}")

    return seat


def held_by(game: PassingGame, seat: int) -> CardsOrJokers:
    """The cards one seat holds, as the rules read them."""
    return cards_of(game.board.zone(hand_of(seat)))


def every_hand(game: PassingGame) -> tuple[CardsOrJokers, ...]:
    """Every seat's cards, which is what a refused move is read against."""
    return tuple(held_by(game, seat) for seat in range(game.players))


def exchange(game: PassingGame, index: int) -> Transaction[PassingState]:
    """The seat on turn gives up the card at that position for the top of the pile."""
    seat = seat_on_turn(game)
    return game.submit(
        Move(player=seat, action=Take(group=PILE, indices=frozenset({index}))),
        base_seq=game.head,
    )


def pass_on(game: PassingGame, index: int) -> Transaction[PassingState]:
    """The seat on turn passes the card at that position to the seat next round the table."""
    seat = seat_on_turn(game)
    return game.submit(
        Move(
            player=seat,
            action=Give(target_player=next_seat(seat, game.players), indices=frozenset({index})),
        ),
        base_seq=game.head,
    )


def with_the_pile_run_out(game: PassingGame) -> Position[PassingState]:
    """The table as it stands, its pile emptied onto the stack, which is where an exhausted pile is answered.

    A win falls to a hand the moment it reads one, so no run of play empties a pile of forty-odd cards, and the
    rules answering an exhausted one are read against a position built to hold that. Every hook takes the
    position it works on, so one built here is answered exactly as the table's own is, and the cards move
    between two zones rather than out of the game, which leaves the board holding the deck it started from.
    """
    board = game.board
    pile, stack = board.zone(PILE), board.zone(STACK)
    return game.position.with_board(
        board.with_zones(
            pile.with_cards(()),
            stack.with_cards(stack.cards + pile.cards),
        ),
    )


def play_out(game: PassingGame, choose: Chooser) -> None:
    """Drive a match to rest, the chooser picking among the moves the rules list."""
    while True:
        moves = game.legal_moves(game.position)
        if moves:
            game.submit(choose(moves), base_seq=game.head)
        elif not game.settle():
            return


def play_to_a_win(game: PassingGame, choose: Chooser) -> int:
    """Drive the table until a round is won, answering with the seat that won it.

    A win needs no move of its own, so this plays on until the cursor names a winner, which is the transaction
    a dealt or completed hand reading three alike lands in.

    Raises:
        ValueError: when the table comes to rest with no round won, which a standing moved by wins alone
            leaves out of reach.
    """
    while True:
        winner = game.state.winner
        if winner is not None:
            return winner

        moves = game.legal_moves(game.position)
        if moves:
            game.submit(choose(moves), base_seq=game.head)
        elif not game.settle():
            raise ValueError(f"The table came to rest at sequence {game.head} with no round won")
