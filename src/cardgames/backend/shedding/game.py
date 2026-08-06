from random import Random
from typing import ClassVar

from cardgames.backend.shedding.rules import (
    AWARD,
    HAND_SIZE,
    NO_CARDS,
    ROUND_POINT,
    SEATS_LEAST,
    SEATS_MOST,
    SHED_LEAST,
    SHEDDING_RANKING,
    drawn_from,
    may_act,
)
from cardgames.backend.shedding.state import SheddingPhase, SheddingState
from cardgames.backend.shedding.zones import STOCK, shedding_zones
from cardwork.decks.deck import Deck
from cardwork.decks.standard import confirm_standard_deck
from cardwork.effects.effects import Effects, MoveCards, SetState
from cardwork.exceptions import IllegalMove
from cardwork.games.capacity import Capacity
from cardwork.games.dealt import confirm_dealt
from cardwork.games.intents import Intents
from cardwork.moves.actions import Discard, Take
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.rounds.game import RoundGame
from cardwork.rounds.redeal import Redeal
from cardwork.rounds.seating import following, next_seat, rotation
from cardwork.rounds.state import MatchPhase
from cardwork.states.state import NOTHING
from cardwork.zones.zone import Zones
from cardwork.zones.zones import DISCARD, HANDS


class SheddingGame(RoundGame[SheddingState]):
    """A match of rounds in which a turn sheds cards of one rank, and the shortest hand takes the round.

    A round deals every seat four cards and runs the turns those hold. **A turn either sheds or draws.** A shed
    lays two cards or more of one rank face up on the discard, so four alike go out in one turn and a pair at a
    time takes two; `rules.SHEDDING_RANKING` holds that rule whole, as the two, three and four of a rank one
    standard deck reaches. A draw takes one card of the stock into the hand. Either way the turn passes to the
    next seat.

    That is the whole of the choice, and it is a real one: a seat holding a pair may lay it down or hold it back
    and fish for the third of its rank, which a hand is only ever worth doing while the stock has cards left to
    hand over. A hand holding three of a rank offers both of its pairs beside the three of them, so a set is
    chosen as well as found.

    **The round goes to the seat left holding the fewest cards.** A seat that sheds its last card holds none,
    which is the fewest a hand runs to, so going out takes the round on the spot and closes it. Otherwise the
    round runs until the stock has run out and no seat holds a set left to shed — a seat with neither is passed
    over — and the shortest hand at the table takes it, every one of them where several stand equally short.

    The match runs to the conclusion its table was opened with, which is a count of rounds where a match of this
    is played to one.

        game = SheddingGame(players=3, deck=standard_deck(), conclusion=Conclusion(rounds=3), rng=Random(7))
    """

    capacity: ClassVar[Capacity] = Capacity(least=SEATS_LEAST, most=SEATS_MOST)
    intents: ClassVar[Intents[Discard | Take]] = Intents(Discard, Take)

    def zones(self, players: int, deck: Deck) -> Zones:
        return shedding_zones(players, deck)

    def _validate_initial_deck(self, deck: Deck) -> None:
        confirm_standard_deck(deck)

    def initial_state(self, players: int) -> SheddingState:
        return SheddingState(
            phase=MatchPhase.BETWEEN_ROUNDS,
            points=(NOTHING,) * players,
            award=AWARD,
        )

    def _final_validation(self, position: Position[SheddingState]) -> None:
        """Confirm the deal left every seat the four cards it is dealt, which its draws then build on.

        Raises:
            GameValidationError: when a hand holds a number of cards other than the deal gives it.
        """
        confirm_dealt(position, HANDS, HAND_SIZE)

    def deal_round(
        self,
        position: Position[SheddingState],
        leader: int,
        rng: Random,
    ) -> Effects[SheddingState]:
        """Every card gathered and shuffled, then four dealt to each seat from the leader round the table."""
        counts = HANDS.dealt(HAND_SIZE, rotation(leader, position.players))
        return Redeal(position, pile=STOCK, face_down=True).effects(counts, rng)

    def opening_state(
        self,
        position: Position[SheddingState],
        leader: int,
    ) -> SheddingState:
        """The turn the round opens on, which the seat leading it always has its draw to take."""
        return position.state.with_changes(
            phase=SheddingPhase.SHEDDING,
            to_act=leader,
            winner=None,
        )

    def advance_round(
        self,
        position: Position[SheddingState],
        move: Move | None,
        rng: Random,
    ) -> Effects[SheddingState]:
        """The cursor a turn leaves the round on, and the turn a seat with nothing to do is passed over in.

        A move answers for itself: the cards are where the turn put them, and either the seat has gone out or
        the turn travels on. A settlement pass answers for a seat holding no set with the stock run out, which
        is the one way a turn falls to nobody, and closes the round where that is every seat.
        """
        if move is None:
            return self._standing(position)

        return (SetState(state=self._acted(position, move)),)

    def round_over(self, position: Position[SheddingState]) -> bool:
        return position.state.phase == SheddingPhase.DECIDED

    def validate(self, position: Position[SheddingState], move: Move) -> None:
        """Read the move as one of the two a turn is made of, and hold it to the rules of that one.

        Raises:
            IllegalMove: when the move breaks a rule of the intent it carries.
        """
        match self.intents.read(move):
            case Discard() as shedding:
                self._validate_shed(position, move.player, shedding)

            case Take() as drawing:
                self._validate_draw(position, move.player, drawing)

    def expand(
        self,
        position: Position[SheddingState],
        move: Move,
        rng: Random,
    ) -> Effects[SheddingState]:
        """The cards a turn moves: the set laid on the discard, or the card taken off the stock."""
        match self.intents.read(move):
            case Discard() as shedding:
                return self._laid(move.player, shedding)

            case Take():
                return self._drew(position, move.player)

    def moves_of(self, position: Position[SheddingState], seat: int) -> Moves:
        """Every set one seat may shed, and the draw it may take while the stock holds a card.

        A triplet in hand lists the three of them and each of their pairs, so a client reading this list reads
        the whole choice a turn carries. A seat holding no set with the stock run out is offered nothing, which
        is the seat a settlement pass hands the turn past.
        """
        sheds = tuple(
            Move(player=seat, action=Discard(group=HANDS.name, indices=places))
            for places in SHEDDING_RANKING.selections(position.board.cards(HANDS.of(seat)))
        )
        if not position.board.holds(STOCK):
            return sheds

        drawn = drawn_from(position.board.count(STOCK))
        return sheds + (Move(player=seat, action=Take(group=STOCK, indices=drawn)),)

    def _validate_shed(
        self,
        position: Position[SheddingState],
        seat: int,
        shedding: Discard,
    ) -> None:
        """Confirm the set is two cards or more of the seat's own hand, reading as the one rank.

        Raises:
            IllegalMove: when the shed names another group, names fewer than two cards, names a position
                beyond the hand, or names cards reading as more than one rank.
        """
        if shedding.group != HANDS.name:
            raise IllegalMove(f"Seat {seat} sheds from its {HANDS.name}, and named {shedding.group!r}")

        if len(shedding.indices) < SHED_LEAST:
            raise IllegalMove(f"Seat {seat} sheds {SHED_LEAST} cards or more, and named {len(shedding.indices)}")

        held = position.board.count(HANDS.of(seat))
        if max(shedding.indices) >= held:
            raise IllegalMove(f"Seat {seat} named position {max(shedding.indices)} of a hand holding {held}")

        shed = position.board.taken(HANDS.of(seat), shedding.indices)
        if SHEDDING_RANKING.exactly(shed) is None:
            shown = " ".join(str(card) for card in shed)
            raise IllegalMove(f"Seat {seat} sheds cards reading as one rank, and named {shown}")

    def _validate_draw(
        self,
        position: Position[SheddingState],
        seat: int,
        drawing: Take,
    ) -> None:
        """Confirm the draw takes the card at the end of a stock still holding one.

        Raises:
            IllegalMove: when the draw names another zone, when the stock has run out, or when it names a
                position other than the card lying at the end of it.
        """
        if drawing.group != STOCK:
            raise IllegalMove(f"Seat {seat} draws from the {STOCK}, and named {drawing.group!r}")

        stock = position.board.count(STOCK)
        if stock == NO_CARDS:
            raise IllegalMove(f"Seat {seat} draws from a {STOCK} that has run out")

        if drawing.indices != drawn_from(stock):
            raise IllegalMove(
                f"Seat {seat} draws position {sorted(drawn_from(stock))} of the {STOCK}, "
                f"and named {sorted(drawing.indices)}"
            )

    def _laid(self, seat: int, shedding: Discard) -> Effects[SheddingState]:
        """The set laid face up on the discard, where the whole table reads what a turn shed."""
        return (
            MoveCards(
                source=HANDS.of(seat),
                indices=shedding.indices,
                target=DISCARD,
                face_down=False,
            ),
        )

    def _drew(
        self,
        position: Position[SheddingState],
        seat: int,
    ) -> Effects[SheddingState]:
        """The card at the end of the stock taken into the hand, face down as everything in a hand is."""
        return (
            MoveCards(
                source=STOCK,
                indices=drawn_from(position.board.count(STOCK)),
                target=HANDS.of(seat),
                face_down=True,
            ),
        )

    def _may_act(
        self,
        position: Position[SheddingState],
        seat: int,
    ) -> bool:
        """Whether one seat has a turn to take from this position."""
        return may_act(
            position.board.cards(HANDS.of(seat)),
            position.board.count(STOCK),
        )

    def _acted(
        self,
        position: Position[SheddingState],
        move: Move,
    ) -> SheddingState:
        """The cursor the round stands on once a turn has landed: the round closed on a seat out, or the turn passed on."""
        if not position.board.holds(HANDS.of(move.player)):
            return self._decided(position, winner=move.player)

        return position.state.with_changes(to_act=next_seat(move.player, position.players))

    def _standing(self, position: Position[SheddingState]) -> Effects[SheddingState]:
        """What the round owes with no move behind the question, which is a turn nobody there can take.

        The turn stands with a seat that may act, and a seat holding no set once the stock has run out may
        not, so the turn travels on to the next seat that can. A round where that is every seat is decided.
        """
        seat = position.state.current
        if seat is None or self._may_act(position, seat):
            return ()

        return self._passed_over(position, seat)

    def _passed_over(
        self,
        position: Position[SheddingState],
        seat: int,
    ) -> Effects[SheddingState]:
        """The turn handed to the next seat that may act, and the round decided where no seat may."""
        onwards = following(
            seat,
            position.players,
            lambda other: self._may_act(position, other),
            including=False,
        )
        if onwards is None:
            return (SetState(state=self._decided(position, winner=None)),)

        return (SetState(state=position.state.with_changes(to_act=onwards)),)

    def _decided(
        self,
        position: Position[SheddingState],
        winner: int | None,
    ) -> SheddingState:
        """The round closed: the award to the shortest hand at the table, and the seat that went out where one did.

        One rule scores either close. A seat shedding its last card is the shortest hand there can be, and a
        round the stock ran out of is read the same way, so the award follows from the hands as they lie.

        Args:
            position: the table as the round leaves it.
            winner: the seat that shed its last card, and None for a round the stock ran out of.
        """
        shortest = position.fewest(HANDS)
        return position.state.at_rest(
            SheddingPhase.DECIDED,
            winner=winner,
            round_points=tuple(ROUND_POINT if seat in shortest else NOTHING for seat in position.seats),
        )
