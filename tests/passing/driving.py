from collections.abc import Callable
from random import Random
from typing import Final

from cardgames.passing.game import PassingGame
from cardgames.passing.rules import PassingClaim, declares
from cardgames.passing.state import PassingState
from cardgames.passing.zones import PILE, hand_of
from cardwork.cards.game import CardsOrJokers
from cardwork.decks.deck import Deck
from cardwork.decks.standard import standard_decks
from cardwork.moves.actions import Declare, Give, Take
from cardwork.moves.move import Move, Moves
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


def claim_a_win(game: PassingGame) -> Transaction[PassingState]:
    """The seat on turn claims a win of its whole hand."""
    seat = seat_on_turn(game)
    return game.submit(
        Move(player=seat, action=Declare(claim=PassingClaim.WIN, indices=frozenset())),
        base_seq=game.head,
    )


def until_the_turn_holds_no_win(game: PassingGame) -> int:
    """The seat on turn once its hand holds a win back, the card passing on until such a seat has the turn."""
    while declares(held_by(game, seat_on_turn(game))):
        pass_on(game, FIRST_CARD)

    return seat_on_turn(game)


def exchange_until_the_pile_runs_out(game: PassingGame) -> None:
    """Every turn spends its exchange, until the pile they draw from holds nothing.

    The turn that empties the pile is left standing open, which is where the rules meet a pile run out.
    """
    while game.board.zone(PILE).cards:
        exchange(game, FIRST_CARD)
        if game.board.zone(PILE).cards:
            pass_on(game, FIRST_CARD)


def play_out(game: PassingGame, choose: Chooser) -> None:
    """Drive a match to rest, the chooser picking among the moves the rules list."""
    while True:
        moves = game.legal_moves(game.position)
        if moves:
            game.submit(choose(moves), base_seq=game.head)
        elif not game.settle():
            return


def play_to_a_claim(game: PassingGame, choose: Chooser) -> int:
    """Drive the table until a seat claims the win it holds, answering with the seat that claimed it.

    A claim is taken as soon as the rules list one, and every other move comes from the chooser, so a round
    that runs its pile out carries on into the next.

    Raises:
        ValueError: when the table comes to rest with no claim made, which a standing moved by wins alone
            leaves out of reach.
    """
    while True:
        moves = game.legal_moves(game.position)
        claims = tuple(move for move in moves if isinstance(move.action, Declare))
        if claims:
            game.submit(claims[FIRST_CARD], base_seq=game.head)
            return claims[FIRST_CARD].player

        if moves:
            game.submit(choose(moves), base_seq=game.head)
        elif not game.settle():
            raise ValueError(f"The table came to rest at sequence {game.head} with no seat claiming a win")
