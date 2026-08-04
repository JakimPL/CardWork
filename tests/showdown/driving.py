from collections.abc import Callable
from random import Random
from typing import Final

from cardgames.backend.showdown.game import ShowdownGame
from cardgames.backend.showdown.state import ShowdownState
from cardgames.backend.showdown.zones import Holding, hand_of, tray_of, zone_of
from cardwork.cards.game import CardsOrJokers
from cardwork.decks.deck import Deck
from cardwork.decks.standard import standard_deck
from cardwork.moves.actions import Play
from cardwork.moves.move import Move, Moves
from cardwork.rounds.conclusion import Conclusion
from cardwork.transactions.transaction import Transaction, Transactions
from cardwork.zones.zone import ZoneId, cards_of
from cardwork.zones.zones import DISCARD

SEATS: Final[int] = 3
TWO_SEATS: Final[int] = 2
FULL_TABLE: Final[int] = 5
ROUNDS: Final[int] = 2
SEED: Final[int] = 20260804
FIRST_CARD: Final[int] = 0
DECK: Final[Deck] = standard_deck()

type Chooser = Callable[[Moves], Move]


def a_match(players: int, rounds: int, seed: int) -> ShowdownGame:
    """A fresh table of that many seats, built for that many rounds, drawing from a generator of that seed."""
    return ShowdownGame(players=players, deck=DECK, conclusion=Conclusion(rounds=rounds), rng=Random(seed))


def commit(game: ShowdownGame, seat: int, holding: Holding, index: int) -> Transaction[ShowdownState]:
    """One seat commits the card at that position of that holding."""
    return game.submit(
        Move(player=seat, action=Play(group=holding, indices=frozenset({index}))),
        base_seq=game.head,
    )


def a_holding_of(game: ShowdownGame, seat: int) -> Holding:
    """The holding a seat still has a card in, which is its hand for as long as that holds one."""
    return Holding.HAND if game.board.zone(hand_of(seat)).cards else Holding.BLIND


def commit_the_turn(game: ShowdownGame, holding: Holding) -> Transactions[ShowdownState]:
    """Every seat owing a commitment seals the first card of that holding, and the table settles after them."""
    for seat in sorted(game.state.to_act):
        commit(game, seat, holding, FIRST_CARD)

    return game.settle()


def commit_whatever_is_held(game: ShowdownGame) -> Transactions[ShowdownState]:
    """Every seat owing a commitment seals its first hand card, or a blind one once its hand has run out."""
    for seat in sorted(game.state.to_act):
        commit(game, seat, a_holding_of(game, seat), FIRST_CARD)

    return game.settle()


def play_a_round(game: ShowdownGame) -> Transactions[ShowdownState]:
    """Every turn of the round in play, answering with the transactions the last of them settled."""
    playing = game.state.round_number
    settled: Transactions[ShowdownState] = ()
    while game.state.round_number == playing and game.state.to_act:
        settled = commit_whatever_is_held(game)

    return settled


def play_out(game: ShowdownGame, choose: Chooser) -> None:
    """Drive a match to rest, the chooser picking among the moves the rules list."""
    while True:
        moves = game.legal_moves(game.position)
        if moves:
            game.submit(choose(moves), base_seq=game.head)
        elif not game.settle():
            return


def held_by(game: ShowdownGame, seat: int) -> CardsOrJokers:
    """The cards one seat reads in its hand."""
    return cards_of(game.board.zone(hand_of(seat)))


def holding_of(game: ShowdownGame, seat: int, holding: Holding) -> CardsOrJokers:
    """The cards one of a seat's holdings holds, as the rules read them."""
    return cards_of(game.board.zone(zone_of(holding, seat)))


def sealed_by(game: ShowdownGame, seat: int) -> CardsOrJokers:
    """The card one seat has committed, which lies in its tray until the turn turns over."""
    return cards_of(game.board.zone(tray_of(seat)))


def revealed(game: ShowdownGame) -> CardsOrJokers:
    """Every card the round has turned over, in the order the turns revealed them."""
    return cards_of(game.board.zone(DISCARD))


def every_zone(game: ShowdownGame) -> dict[ZoneId, CardsOrJokers]:
    """Every card on the table, filed under the zone holding it, which is what a refusal is read against."""
    return {zone_id: cards_of(zone) for zone_id, zone in game.board.zones.items()}
