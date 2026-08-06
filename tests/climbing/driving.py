from collections.abc import Callable, Sequence
from random import Random
from typing import Final

from cardgames.backend.climbing.game import ClimbingGame
from cardgames.backend.climbing.rules import CLIMBING_RANKING, POINTS
from cardgames.backend.climbing.state import ClimbingPhase, ClimbingState
from cardwork.cards.game import CardOrJoker, CardsOrJokers
from cardwork.combinations.combination import Combination
from cardwork.decks.deck import Deck, Indices
from cardwork.decks.decks import to_game_cards
from cardwork.decks.standard import standard_deck
from cardwork.models.held import held
from cardwork.moves.actions import Pass, Play
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.rounds.conclusion import Conclusion
from cardwork.transactions.transaction import Transaction
from cardwork.zones.zone import ZoneId
from cardwork.zones.zones import DISCARD, HANDS, STACK

SEATS: Final[int] = 3
TWO_SEATS: Final[int] = 2
FOUR_SEATS: Final[int] = 4
FULL_TABLE: Final[int] = 5
ROUNDS: Final[int] = 2
SEED: Final[int] = 20260806
FIRST_MOVE: Final[int] = 0
NO_PASSES: Final[frozenset[int]] = frozenset()
DECK: Final[Deck] = standard_deck()

type Chooser = Callable[[Moves], Move]


def a_match(players: int, rounds: int, seed: int) -> ClimbingGame:
    """A fresh table of that many seats, built for that many rounds, drawing from a generator of that seed."""
    return ClimbingGame(players=players, deck=DECK, conclusion=Conclusion(rounds=rounds), rng=Random(seed))


def seat_on_turn(game: ClimbingGame) -> int:
    """The seat the turn stands with at the table.

    Raises:
        ValueError: when the turn stands with several seats or with none, which a round in play never reaches.
    """
    return turn_of(game.position)


def turn_of(position: Position[ClimbingState]) -> int:
    """The seat the turn stands with on one table, which is what a run of `step` reads its next move off.

    Raises:
        ValueError: when the turn stands with several seats or with none, which a round in play never reaches.
    """
    seat = position.state.current
    if seat is None:
        raise ValueError(f"One seat holds the turn, and it stands with {sorted(position.state.to_act)}")

    return seat


def held_by(game: ClimbingGame, seat: int) -> CardsOrJokers:
    """The cards one seat holds, as the rules read them."""
    return game.board.cards(HANDS.of(seat))


def every_hand(game: ClimbingGame) -> tuple[CardsOrJokers, ...]:
    """Every seat's cards, which is what a refused move is read against."""
    return tuple(held_by(game, seat) for seat in range(game.players))


def caught_with(cards: CardsOrJokers) -> int:
    """The penalty a seat left holding those cards takes, which is what every one of them is worth."""
    return POINTS.total(cards)


def a_combination_of(cards: CardsOrJokers) -> Combination:
    """The cards read as the combination they are, which is the reading a cursor carries on the table.

    Raises:
        LogicError: when the cards read as no combination this game is played by.
    """
    return held(CLIMBING_RANKING.exactly(cards), f"combination stands in {cards}")


def places_of(cards: CardsOrJokers, wanted: CardOrJoker) -> Indices:
    """The one place a card stands at in a run holding it, as a play names it.

    Raises:
        ValueError: when the run holds no such card.
    """
    return frozenset({cards.index(wanted)})


def a_play(seat: int, places: Indices) -> Move:
    """One seat playing the cards standing at those positions of its own hand."""
    return Move(player=seat, action=Play(group=HANDS.name, indices=places))


def a_pass(seat: int) -> Move:
    """One seat giving its turn up over the combination the table stands on."""
    return Move(player=seat, action=Pass())


def play_from(game: ClimbingGame, places: Indices) -> Transaction[ClimbingState]:
    """The seat on turn plays the cards standing at those positions of its hand."""
    return game.submit(a_play(seat_on_turn(game), places), base_seq=game.head)


def give_the_turn_up(game: ClimbingGame) -> Transaction[ClimbingState]:
    """The seat on turn passes over the combination the table stands on."""
    return game.submit(a_pass(seat_on_turn(game)), base_seq=game.head)


def a_lead_of(
    game: ClimbingGame,
    hands: Sequence[CardsOrJokers],
    leader: int,
) -> Position[ClimbingState]:
    """The table laid out afresh on a lead: those hands, that seat to put down a combination of its choosing.

    Args:
        game: the table the position is built from, whose zones and deck it keeps.
        hands: the cards each seat is to hold, in seat order.
        leader: the seat the lead is to stand with.
    """
    return _laid_out(
        game,
        hands,
        game.state.with_changes(phase=ClimbingPhase.LEAD, to_act=leader, on_table=None, passed=NO_PASSES),
        played=(),
    )


def an_opening_of(
    game: ClimbingGame,
    hands: Sequence[CardsOrJokers],
    opener: int,
) -> Position[ClimbingState]:
    """The table laid out afresh on the turn a match opens with: those hands, that seat to put down the first one.

    Args:
        game: the table the position is built from, whose zones and deck it keeps.
        hands: the cards each seat is to hold, in seat order, the opening card among them.
        opener: the seat the opening turn is to stand with, which is the one holding that card.
    """
    return _laid_out(
        game,
        hands,
        game.state.with_changes(phase=ClimbingPhase.OPENING, to_act=opener, on_table=None, passed=NO_PASSES),
        played=(),
    )


def a_contest_of(
    game: ClimbingGame,
    hands: Sequence[CardsOrJokers],
    turn: int,
    on_table: Combination,
    passed: frozenset[int],
) -> Position[ClimbingState]:
    """The table laid out afresh mid-contest: those hands, that combination standing face up, those seats out of it.

    Args:
        game: the table the position is built from, whose zones and deck it keeps.
        hands: the cards each seat is to hold, in seat order.
        turn: the seat the turn is to stand with, which answers what the table holds.
        on_table: the combination standing there, whose cards lie on the stack for an answer to climb over.
        passed: the seats that have given their turn up over it.
    """
    return _laid_out(
        game,
        hands,
        game.state.with_changes(phase=ClimbingPhase.FOLLOW, to_act=turn, on_table=on_table, passed=passed),
        played=on_table.cards,
    )


def _laid_out(
    game: ClimbingGame,
    hands: Sequence[CardsOrJokers],
    state: ClimbingState,
    played: CardsOrJokers,
) -> Position[ClimbingState]:
    """The table holding those hands, that much played face up on the stack, and standing on that cursor.

    A contest is decided by combinations the ranking reads at a glance — a pair answered by a higher pair, a
    hand of one card, a table every seat but one has passed over — and no run of play is driven to reach one.
    Every hook takes the position it works on, so a position built here is answered exactly as the table's own
    is, and the cards the hands and the stack leave over lie face down on the discard, which is where a round
    keeps the cards nobody was dealt. So every card of the deck stands in one zone or another, which leaves the
    board holding the deck it was dealt from.
    """
    left = list(game.board.starting_deck)
    for card in (card for hand in hands for card in hand):
        left.remove(card)

    for card in played:
        left.remove(card)

    board = game.board
    laid = tuple(
        board.zone(HANDS.of(seat)).with_cards(to_game_cards(hand, face_down=True)) for seat, hand in enumerate(hands)
    )
    return Position(
        board=board.with_zones(
            *laid,
            board.zone(STACK).with_cards(to_game_cards(played, face_down=False)),
            board.zone(DISCARD).with_cards(to_game_cards(tuple(left), face_down=True)),
        ),
        state=state,
        players=game.players,
    )


def passed_by(
    game: ClimbingGame,
    position: Position[ClimbingState],
    seats: Sequence[int],
) -> Position[ClimbingState]:
    """The table after those seats have each given their turn up, in the order they are named.

    Args:
        game: the table whose rules the passes are read by.
        position: the contest the first of them passes over.
        seats: the seats passing, the turn standing with each as it does.
    """
    for seat in seats:
        position = game.step(position, a_pass(seat), Random(SEED))

    return position


def every_zone(game: ClimbingGame) -> dict[ZoneId, CardsOrJokers]:
    """Every card on the table, filed under the zone holding it, which is what a refusal is read against."""
    return {zone_id: game.board.cards(zone_id) for zone_id in game.board.zones}


def climbing_first(moves: Moves) -> Move:
    """A combination where the turn may put one down, which empties a hand fastest, and the pass otherwise."""
    plays = tuple(move for move in moves if isinstance(move.action, Play))
    return plays[FIRST_MOVE] if plays else moves[FIRST_MOVE]


def passing_first(moves: Moves) -> Move:
    """The pass where the turn may give itself up, which drives the table through its reopened leads."""
    passes = tuple(move for move in moves if isinstance(move.action, Pass))
    return passes[FIRST_MOVE] if passes else moves[FIRST_MOVE]


def play_out(game: ClimbingGame, choose: Chooser) -> None:
    """Drive a match to rest, the chooser picking among the moves the rules list."""
    while True:
        moves = game.legal_moves(game.position)
        if moves:
            game.submit(choose(moves), base_seq=game.head)
        elif not game.settle():
            return


def play_a_round(game: ClimbingGame, choose: Chooser) -> None:
    """Drive the table until the round in play is decided, the chooser picking among the moves the rules list.

    Raises:
        ValueError: when the table comes to rest with the round still standing, which a dealt hand never leaves
            it at.
    """
    while not game.round_over(game.position):
        moves = game.legal_moves(game.position)
        if moves:
            game.submit(choose(moves), base_seq=game.head)
        elif not game.settle():
            raise ValueError(f"The table came to rest at sequence {game.head} with the round undecided")
