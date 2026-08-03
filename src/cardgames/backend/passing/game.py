from random import Random
from typing import Final

from cardgames.backend.passing.rules import (
    HAND_ON_TURN,
    HAND_SIZE,
    NOTHING,
    ROUND_POINT,
    WINNING_LEAD,
    declares,
)
from cardgames.backend.passing.state import PassingPhase, PassingState
from cardgames.backend.passing.zones import PILE, STACK, TOP_OF_THE_PILE, hand_of, passing_zones
from cardwork.decks.deck import Deck, Indices
from cardwork.decks.standard import ONE_DECK, standard_multiplicity
from cardwork.effects.effects import Effects, MoveCards, SetFace, SetState
from cardwork.exceptions import IllegalMove
from cardwork.moves.actions import Give, Take
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.rounds.game import RoundGame
from cardwork.rounds.redeal import Redeal
from cardwork.rounds.seating import next_seat, rotation
from cardwork.rounds.state import MatchPhase
from cardwork.zones.zone import Zones, cards_of

SEATS_LEAST: Final[int] = 2
SEATS_MOST: Final[int] = 8
ONE_CARD: Final[int] = 1
BEST: Final[int] = 0
NEXT_BEST: Final[int] = 1

type PassingIntent = Take | Give


def intent(move: Move) -> PassingIntent:
    """The intent behind a move, which is an exchange with the pile or a pass to the next seat.

    Raises:
        IllegalMove: when the move carries some other intent.
    """
    action = move.action
    if isinstance(action, Take | Give):
        return action

    raise IllegalMove(f"Seat {move.player} exchanges or passes, and offered {action.kind}")


class PassingGame(RoundGame[PassingState]):
    """A match of rounds in which a fourth card circulates and a win falls to the seat whose three read alike.

    A round deals three cards to every seat and a fourth to the seat leading it, so exactly one seat holds four
    at a time and the turn travels with that card. A turn admits one exchange with the top of the pile, the card
    given up going face up on the stack, and closes with a card passed to the next seat.

    A hand of four wins where some three of it read as one rank or as one suit while the four do not, a joker
    standing in for whatever the three asks of it. `rules.declares` holds that rule whole. A win needs no claim:
    a seat holding one has nothing to gain by passing it on, so the rules take it the moment the cards read it,
    turning the hand face up and scoring its seat a point. An exhausted pile draws the round as the turn it ran
    out on closes, and scores nobody. The match belongs to the first seat leading the next best by two points.

        game = PassingGame(players=4, deck=standard_decks(1, black_jokers=1, red_jokers=1), rng=Random(7))
    """

    def __init__(
        self,
        players: int,
        deck: Deck,
        *,
        rng: Random | None = None,
    ) -> None:
        """A table dealt its first round, settled to the point a seat has a turn to take.

        A deal that already reads a win decides its round before any seat acts, so the table settles here until
        it stands on a round with someone to act, which is what every driver and adapter beyond this expects of
        a table it has just opened.
        """
        super().__init__(players, deck, rng=rng)
        self.settle()

    def zones(self, players: int, deck: Deck) -> Zones:
        return passing_zones(players, deck)

    def _validate_players(self, players: int) -> None:
        if not SEATS_LEAST <= players <= SEATS_MOST:
            raise ValueError(f"This game seats {SEATS_LEAST} to {SEATS_MOST} players, and {players} were asked for")

    def _validate_initial_deck(self, deck: Deck) -> None:
        if standard_multiplicity(deck) < ONE_DECK:
            raise ValueError("This game is played with whole standard decks, and any number of jokers besides")

    def _initialize(self, players: int) -> PassingState:
        return PassingState(phase=MatchPhase.BETWEEN_ROUNDS, points=(NOTHING,) * players)

    def _final_validation(self, position: Position[PassingState]) -> None:
        """Confirm the deal left every seat its three cards and the seat leading the round its fourth.

        Raises:
            ValueError: when a hand holds a number of cards other than the deal gives it.
        """
        leader = position.state.led_by
        short = tuple(
            seat
            for seat in range(position.players)
            if len(position.board.zone(hand_of(seat)).cards) != self._dealt(seat, leader)
        )
        if short:
            raise ValueError(f"Seats {short} hold a hand of a size other than the {HAND_SIZE} the deal gives them")

    def deal_round(
        self,
        position: Position[PassingState],
        leader: int,
        rng: Random,
    ) -> Effects[PassingState]:
        """Every card gathered and shuffled, then three dealt to each seat from the leader round the table.

        The leader takes its fourth card with the rest of its hand, which is the card the round circulates.
        """
        counts = {hand_of(seat): self._dealt(seat, leader) for seat in rotation(leader, position.players)}
        return Redeal(position, pile=PILE, face_down=True).effects(counts, rng)

    def opening_state(self, position: Position[PassingState], leader: int) -> PassingState:
        return position.state.with_changes(
            phase=PassingPhase.PASSING,
            to_act=frozenset({leader}),
            swapped=False,
            winner=None,
        )

    def advance_round(
        self,
        position: Position[PassingState],
        move: Move | None,
        rng: Random,
    ) -> Effects[PassingState]:
        """The cursor the round stands on once a seat has acted, and the win the cards may already read.

        A move carries the turn it spends and the turn it hands on, and the win the hand it leaves behind reads
        travels in the same transaction, so a seat is awarded a win in the moment it holds one and no stretch of
        latency stands between the two. A settlement pass answers with the win a fresh deal laid out, which is
        the one no move put there.
        """
        if move is None:
            return self._decided(position)

        acted = self._acted(position, move)
        settled: Effects[PassingState] = (SetState(state=acted),)
        return settled + self._decided(position.with_state(acted))

    def round_over(self, position: Position[PassingState]) -> bool:
        return position.state.phase == PassingPhase.DECIDED

    def match_over(self, position: Position[PassingState]) -> bool:
        """Whether one seat leads the next best by the points a match is won by."""
        points = position.state.points
        standing = sorted(
            points if points is not None else (NOTHING,) * position.players,
            reverse=True,
        )
        return standing[BEST] - standing[NEXT_BEST] >= WINNING_LEAD

    def validate(self, position: Position[PassingState], move: Move) -> None:
        """Read the move as one of the two a turn is made of, and hold it to the rules of that one.

        Raises:
            IllegalMove: when the move carries another intent, or breaks a rule of the intent it carries.
        """
        match intent(move):
            case Take() as exchange:
                self._validate_exchange(position, move.player, exchange)

            case Give() as passing:
                self._validate_pass(position, move.player, passing)

    def expand(
        self,
        position: Position[PassingState],
        move: Move,
        rng: Random,
    ) -> Effects[PassingState]:
        """The cards a move moves: the exchange with the pile, or the pass to the next seat."""
        match intent(move):
            case Take() as exchange:
                return self._exchanged(move.player, exchange.indices)

            case Give() as passing:
                return self._passed(move.player, passing)

    def legal_moves(self, position: Position[PassingState]) -> Moves:
        """Every exchange and pass the seat on turn may make.

        A hand that wins is awarded the round in the transaction that dealt or completed it, so a seat reading
        this list holds no win and has only these two to weigh.
        """
        return tuple(move for seat in sorted(position.state.to_act) for move in self._turn_of(position, seat))

    def _turn_of(self, position: Position[PassingState], seat: int) -> Moves:
        """The moves one seat may make from this position, in the order a turn takes them."""
        held = position.board.zone(hand_of(seat))
        places = tuple(frozenset({index}) for index in range(len(held.cards)))
        exchanges = (
            tuple(Move(player=seat, action=Take(group=PILE, indices=place)) for place in places)
            if self._may_exchange(position)
            else ()
        )
        passes = tuple(
            Move(
                player=seat,
                action=Give(
                    target_player=next_seat(seat, position.players),
                    indices=place,
                ),
            )
            for place in places
        )
        return exchanges + passes

    def _may_exchange(self, position: Position[PassingState]) -> bool:
        """Whether the turn still holds its exchange and the pile a card for it to take."""
        return bool(position.board.zone(PILE).cards) and not position.state.swapped

    def _dealt(self, seat: int, leader: int) -> int:
        """How many cards a seat is dealt: three, and a fourth for the seat leading the round."""
        return HAND_ON_TURN if seat == leader else HAND_SIZE

    def _validate_exchange(
        self,
        position: Position[PassingState],
        seat: int,
        exchange: Take,
    ) -> None:
        """Confirm the exchange is with a pile holding a card, on a turn that has yet to make one.

        Raises:
            IllegalMove: when the exchange names another zone, when the pile has run out, when the turn has
                already exchanged, or when the card given up is other than one card the seat holds.
        """
        if exchange.group != PILE:
            raise IllegalMove(f"Seat {seat} exchanges with the {PILE}, and named {exchange.group!r}")

        if not position.board.zone(PILE).cards:
            raise IllegalMove(f"Seat {seat} exchanges with a pile that has run out")

        if position.state.swapped:
            raise IllegalMove(f"Seat {seat} exchanges once in a turn, and has exchanged in this one")

        self._validate_one_held(position, seat, exchange.indices)

    def _validate_pass(
        self,
        position: Position[PassingState],
        seat: int,
        passing: Give,
    ) -> None:
        """Confirm the pass hands one held card to the seat next round the table.

        Raises:
            IllegalMove: when the pass names another seat, or a card other than one the seat holds.
        """
        following = next_seat(seat, position.players)
        if passing.target_player != following:
            raise IllegalMove(f"Seat {seat} passes to seat {following}, and named seat {passing.target_player}")

        self._validate_one_held(position, seat, passing.indices)

    def _validate_one_held(
        self,
        position: Position[PassingState],
        seat: int,
        indices: Indices,
    ) -> None:
        """Confirm the indices name one card of the seat's own hand.

        Raises:
            IllegalMove: when they name several cards, or a position beyond the hand.
        """
        held = len(position.board.zone(hand_of(seat)).cards)
        if len(indices) != ONE_CARD:
            raise IllegalMove(f"Seat {seat} names one card at a time, and named {len(indices)}")

        if max(indices) >= held:
            raise IllegalMove(f"Seat {seat} named position {max(indices)} of a hand holding {held}")

    def _exchanged(self, seat: int, given_up: Indices) -> Effects[PassingState]:
        """The card given up laid face up on the stack, and the top of the pile taken into the hand.

        The hand gives its card up first, so the position named is the one the seat was reading.
        """
        exchanged: Effects[PassingState] = (
            MoveCards(
                source=hand_of(seat),
                indices=given_up,
                target=STACK,
                face_down=False,
            ),
            MoveCards(
                source=PILE,
                indices=frozenset({TOP_OF_THE_PILE}),
                target=hand_of(seat),
                face_down=True,
            ),
        )
        return exchanged

    def _passed(self, seat: int, passing: Give) -> Effects[PassingState]:
        """The card handed on to the next seat, arriving face down as everything in a hand does."""
        passed: Effects[PassingState] = (
            MoveCards(
                source=hand_of(seat),
                indices=passing.indices,
                target=hand_of(passing.target_player),
                face_down=True,
            ),
        )
        return passed

    def _decided(self, position: Position[PassingState]) -> Effects[PassingState]:
        """The win the hand on turn reads, shown and scored, or nothing where the hand holds none.

        A win asks nothing of the seat holding it: passing it on gives it up and gains that seat nothing, so
        there is no decision here for a move to carry and the rules take the win as soon as the cards read it.
        A hand of three cards never reads one, which leaves every seat off turn out of this.
        """
        seat = position.state.current
        if seat is None:
            return ()

        held = position.board.zone(hand_of(seat))
        if not declares(cards_of(held)):
            return ()

        return self._shown(position, seat) + (SetState(state=self._won_by(position, seat)),)

    def _shown(
        self,
        position: Position[PassingState],
        seat: int,
    ) -> Effects[PassingState]:
        """The winning hand turned face up, so the table reads the win the round closed on."""
        held = len(position.board.zone(hand_of(seat)).cards)
        shown: Effects[PassingState] = (
            SetFace(
                zone=hand_of(seat),
                indices=frozenset(range(held)),
                face_down=False,
            ),
        )
        return shown

    def _acted(
        self,
        position: Position[PassingState],
        move: Move,
    ) -> PassingState:
        """The cursor the round stands on once this move has landed."""
        match intent(move):
            case Take():
                return position.state.with_changes(swapped=True)

            case Give():
                return self._handed_on(position, move.player)

    def _handed_on(
        self,
        position: Position[PassingState],
        giver: int,
    ) -> PassingState:
        """The turn a pass hands to the next seat, and the round drawn where the pile has run out.

        A turn closes on its pass, so the exchange that empties the pile is still awarded the win it drew.
        """
        if not position.board.zone(PILE).cards:
            return self._drawn(position)

        return position.state.with_changes(
            to_act=frozenset({next_seat(giver, position.players)}),
            swapped=False,
        )

    def _drawn(self, position: Position[PassingState]) -> PassingState:
        """The round decided by an exhausted pile, which scores every seat the nothing its tally already reads."""
        return position.state.with_changes(phase=PassingPhase.DECIDED, to_act=frozenset())

    def _won_by(
        self,
        position: Position[PassingState],
        winner: int,
    ) -> PassingState:
        """The round decided by a hand that wins, which scores its winner the point a round is worth."""
        return position.state.with_changes(
            phase=PassingPhase.DECIDED,
            to_act=frozenset(),
            winner=winner,
            round_points=tuple(ROUND_POINT if seat == winner else NOTHING for seat in range(position.players)),
        )
