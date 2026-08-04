from collections.abc import Callable, Sequence
from random import Random
from typing import Final

from cardgames.backend.shedding.game import SheddingGame
from cardgames.backend.shedding.rules import drawn_from, sets_in
from cardgames.backend.shedding.state import SheddingState
from cardgames.backend.shedding.zones import HAND, STOCK
from cardwork.cards.game import CardsOrJokers
from cardwork.decks.deck import Deck, Indices
from cardwork.decks.decks import to_game_cards
from cardwork.decks.standard import standard_deck
from cardwork.moves.actions import Discard, Take
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.rounds.conclusion import Conclusion
from cardwork.transactions.transaction import Transaction
from cardwork.zones.zone import ZoneId, cards_of, hand_of
from cardwork.zones.zones import DISCARD

SEATS: Final[int] = 3
TWO_SEATS: Final[int] = 2
FULL_TABLE: Final[int] = 6
ROUNDS: Final[int] = 2
SEED: Final[int] = 20260804
FIRST_CARD: Final[int] = 0
DECK: Final[Deck] = standard_deck()

type Chooser = Callable[[Moves], Move]


def a_match(players: int, rounds: int, seed: int) -> SheddingGame:
    """A fresh table of that many seats, built for that many rounds, drawing from a generator of that seed."""
    return SheddingGame(players=players, deck=DECK, conclusion=Conclusion(rounds=rounds), rng=Random(seed))


def seat_on_turn(game: SheddingGame) -> int:
    """The seat the turn stands with.

    Raises:
        ValueError: when the turn stands with several seats or with none, which a round in play never reaches.
    """
    seat = game.state.current
    if seat is None:
        raise ValueError(f"One seat holds the turn, and it stands with {sorted(game.state.to_act)}")

    return seat


def held_by(game: SheddingGame, seat: int) -> CardsOrJokers:
    """The cards one seat holds, as the rules read them."""
    return cards_of(game.board.zone(hand_of(seat)))


def every_hand(game: SheddingGame) -> tuple[CardsOrJokers, ...]:
    """Every seat's cards, which is what a refused move is read against."""
    return tuple(held_by(game, seat) for seat in range(game.players))


def stocked(game: SheddingGame) -> int:
    """How many cards the stock still holds."""
    return len(game.board.zone(STOCK).cards)


def a_shed(seat: int, places: Indices) -> Move:
    """One seat shedding the cards standing at those positions of its own hand."""
    return Move(player=seat, action=Discard(group=HAND, indices=places))


def a_draw(seat: int, stock: int) -> Move:
    """One seat drawing the card at the end of a stock holding that many."""
    return Move(player=seat, action=Take(group=STOCK, indices=drawn_from(stock)))


def shed_from(game: SheddingGame, places: Indices) -> Transaction[SheddingState]:
    """The seat on turn sheds the cards standing at those positions of its hand."""
    return game.submit(a_shed(seat_on_turn(game), places), base_seq=game.head)


def draw(game: SheddingGame) -> Transaction[SheddingState]:
    """The seat on turn draws the card at the end of the stock."""
    return game.submit(a_draw(seat_on_turn(game), stocked(game)), base_seq=game.head)


def left_over(hands: Sequence[CardsOrJokers]) -> int:
    """How many cards of the deck those hands leave, which is the stock of a table holding nothing shed."""
    return len(DECK) - sum(len(hand) for hand in hands)


def a_set_held_by(game: SheddingGame, seat: int) -> Indices | None:
    """The first set the seat's hand holds, and None where it holds none."""
    sets = sets_in(held_by(game, seat))
    return sets[FIRST_CARD] if sets else None


def a_table_of(
    game: SheddingGame,
    hands: Sequence[CardsOrJokers],
    stock: int,
    turn: int,
) -> Position[SheddingState]:
    """The table laid out afresh: those hands, that many cards left in the stock, the rest of the deck shed.

    A round is decided by hands the rules can read at a glance — a pair standing alone, a hand of odd cards, two
    seats as short as one another — and no run of play is driven to reach one. Every hook takes the position it
    works on, so a position built here is answered exactly as the table's own is, and every card of the deck
    stands in one zone or another, which leaves the board holding the deck it was dealt from.

    Args:
        game: the table the position is built from, whose zones and deck it keeps.
        hands: the cards each seat is to hold, in seat order.
        stock: how many of the cards left over stay in the stock, the rest lying shed on the discard.
        turn: the seat the turn is to stand with.
    """
    left = list(game.board.starting_deck)
    for card in (card for hand in hands for card in hand):
        left.remove(card)

    board = game.board
    laid = tuple(
        board.zone(hand_of(seat)).with_cards(to_game_cards(hand, face_down=True)) for seat, hand in enumerate(hands)
    )
    return Position(
        board=board.with_zones(
            *laid,
            board.zone(STOCK).with_cards(to_game_cards(tuple(left[:stock]), face_down=True)),
            board.zone(DISCARD).with_cards(to_game_cards(tuple(left[stock:]), face_down=False)),
        ),
        state=game.state.with_changes(to_act=frozenset({turn})),
        players=game.players,
    )


def every_zone(game: SheddingGame) -> dict[ZoneId, CardsOrJokers]:
    """Every card on the table, filed under the zone holding it, which is what a refusal is read against."""
    return {zone_id: cards_of(zone) for zone_id, zone in game.board.zones.items()}


def shedding_first(moves: Moves) -> Move:
    """A set where the turn holds one, and the draw where it holds none, which empties a hand fastest."""
    sheds = tuple(move for move in moves if isinstance(move.action, Discard))
    return sheds[FIRST_CARD] if sheds else moves[FIRST_CARD]


def play_to_a_shed(game: SheddingGame) -> None:
    """Drive the table until a set lies face up on the discard, shedding wherever a turn can.

    Raises:
        ValueError: when the table comes to rest with nothing shed, which a deck of pairs never leaves it at.
    """
    while not game.board.zone(DISCARD).cards:
        moves = game.legal_moves(game.position)
        if moves:
            game.submit(shedding_first(moves), base_seq=game.head)
        elif not game.settle():
            raise ValueError(f"The table came to rest at sequence {game.head} with nothing shed")


def play_out(game: SheddingGame, choose: Chooser) -> None:
    """Drive a match to rest, the chooser picking among the moves the rules list."""
    while True:
        moves = game.legal_moves(game.position)
        if moves:
            game.submit(choose(moves), base_seq=game.head)
        elif not game.settle():
            return
