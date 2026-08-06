from random import Random
from typing import ClassVar, Final

from cardgames.backend.showdown.rules import (
    AWARD,
    BLIND_SIZE,
    FIRST_TURN,
    HAND_SIZE,
    ONE_CARD,
    ONE_TURN,
    SEATS_LEAST,
    SEATS_MOST,
    awarded,
    taken_by,
    turn_points,
)
from cardgames.backend.showdown.state import ShowdownPhase, ShowdownState
from cardgames.backend.showdown.zones import (
    BLINDS,
    HOLDINGS,
    SEALED_CARD,
    STOCK,
    TRAYS,
    showdown_zones,
)
from cardwork.decks.deck import Deck
from cardwork.decks.standard import confirm_standard_deck
from cardwork.effects.effects import Effects, MoveCards, SetState
from cardwork.exceptions import IllegalMove
from cardwork.games.capacity import Capacity
from cardwork.games.dealt import confirm_dealt
from cardwork.games.intents import Intents
from cardwork.moves.actions import Play
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.rounds.game import RoundGame
from cardwork.rounds.redeal import Redeal
from cardwork.rounds.seating import rotation
from cardwork.rounds.state import MatchPhase
from cardwork.states.state import NOTHING
from cardwork.zones.family import Family, family_named
from cardwork.zones.zone import Zones
from cardwork.zones.zones import DISCARD, HANDS

HOLDING_SIZES: Final[tuple[tuple[Family, int], ...]] = (
    (HANDS, HAND_SIZE),
    (BLINDS, BLIND_SIZE),
)


class ShowdownGame(RoundGame[ShowdownState]):
    """A match of rounds in which every seat commits a card at once, sealed, and the strongest revealed takes them.

    A round deals every seat five cards it reads and five it does not, and runs the ten turns those hold. Each
    turn every seat commits one card — from its hand, or blindly by position from the five it may not read — and
    the cards sit sealed in their trays while the rest of the table acts. They turn over together as the last of
    them lands: the strongest by rank, a tie of rank settled by ♠ ♥ ♦ ♣, takes what every other card revealed is
    worth, pips at face value and jack through ace at ten. A commitment stands once it is sent, since the
    vocabulary this game reads holds nothing that takes one back.

    The round's tally is added into the standing as the round closes, and the match runs to the conclusion its
    table was opened with, which is a count of rounds where a match of this is played to one.

        game = ShowdownGame(players=4, deck=standard_deck(), conclusion=Conclusion(rounds=3), rng=Random(7))
    """

    capacity: ClassVar[Capacity] = Capacity(least=SEATS_LEAST, most=SEATS_MOST)
    intents: ClassVar[Intents[Play]] = Intents(Play)

    def zones(self, players: int, deck: Deck) -> Zones:
        return showdown_zones(players, deck)

    def _validate_initial_deck(self, deck: Deck) -> None:
        confirm_standard_deck(deck)

    def initial_state(self, players: int) -> ShowdownState:
        return ShowdownState(
            phase=MatchPhase.BETWEEN_ROUNDS,
            points=(NOTHING,) * players,
            award=AWARD,
        )

    def _final_validation(self, position: Position[ShowdownState]) -> None:
        """Confirm the deal left every seat five cards to read and five it may not.

        Raises:
            GameValidationError: when a seat holds either of them at a size other than the deal gives it.
        """
        for holding, size in HOLDING_SIZES:
            confirm_dealt(position, holding, size)

    def deal_round(
        self,
        position: Position[ShowdownState],
        leader: int,
        rng: Random,
    ) -> Effects[ShowdownState]:
        """Every card gathered and shuffled, then five dealt to a seat and five blind, from the leader onwards.

        Both holdings of a seat are dealt before the next seat is reached, so the counts name the zones in the
        order the cards leave the stock.
        """
        counts = {
            holding.of(seat): size for seat in rotation(leader, position.players) for holding, size in HOLDING_SIZES
        }
        return Redeal(position, pile=STOCK, face_down=True).effects(counts, rng)

    def opening_state(
        self,
        position: Position[ShowdownState],
        leader: int,
    ) -> ShowdownState:
        """The first turn of the round, which every seat owes a commitment to at once."""
        return position.state.with_changes(
            phase=ShowdownPhase.COMMITTING,
            to_act=position.seats,
            turn_number=FIRST_TURN,
        )

    def advance_round(
        self,
        position: Position[ShowdownState],
        move: Move | None,
        rng: Random,
    ) -> Effects[ShowdownState]:
        """The seat taken out of the turn its commitment answered, and the turn settled once every seat has acted.

        A commitment answers for itself alone: the card is sealed and the turn stands with the seats that have
        yet to commit. The reveal, the points it awards and the turn that follows belong to the settlement after
        the last of them, and land in one transaction, so a client reads a turn whole.
        """
        if move is not None:
            return (SetState(state=self._committed(position, move)),)

        return self._turn_settled(position)

    def round_over(self, position: Position[ShowdownState]) -> bool:
        """Whether both holdings of every seat have run out, which the last turn of a round leaves them at."""
        return not self._committing(position)

    def validate(self, position: Position[ShowdownState], move: Move) -> None:
        """Confirm the commitment names one card of a holding that holds it.

        Raises:
            IllegalMove: when the commitment names neither holding, or names other than one card the named
                holding holds.
        """
        play = self.intents.read(move)
        holding = family_named(HOLDINGS, play.group, move.player)
        held = position.board.count(holding.of(move.player))
        if len(play.indices) != ONE_CARD:
            raise IllegalMove(f"Seat {move.player} commits one card at a time, and named {len(play.indices)}")

        if max(play.indices) >= held:
            raise IllegalMove(
                f"Seat {move.player} named position {max(play.indices)} of a {holding.name} holding {held}"
            )

    def expand(
        self,
        position: Position[ShowdownState],
        move: Move,
        rng: Random,
    ) -> Effects[ShowdownState]:
        """The card sealed face down in the seat's own tray, where it lies unread until the turn turns over."""
        play = self.intents.read(move)
        holding = family_named(HOLDINGS, play.group, move.player)
        return (
            MoveCards(
                source=holding.of(move.player),
                indices=play.indices,
                target=TRAYS.of(move.player),
                face_down=True,
            ),
        )

    def moves_of(
        self,
        position: Position[ShowdownState],
        seat: int,
    ) -> Moves:
        """The commitments one seat may make: a card of its hand, or a position of its blind."""
        return tuple(
            Move(
                player=seat,
                action=Play(group=holding.name, indices=frozenset({index})),
            )
            for holding in HOLDINGS
            for index in range(position.board.count(holding.of(seat)))
        )

    def _committed(
        self,
        position: Position[ShowdownState],
        move: Move,
    ) -> ShowdownState:
        """The turn with this seat's commitment taken out of it, which is all one commitment changes."""
        return position.state.with_changes(to_act=position.state.to_act - {move.player})

    def _turn_settled(
        self,
        position: Position[ShowdownState],
    ) -> Effects[ShowdownState]:
        """The turn turned over, scored and handed on, and nothing at all while a seat has yet to commit.

        The cards turn as they land on the discard, from the leader round the table, so the order they lie in
        states which seat played which and the whole table reads every one of them.
        """
        order = rotation(position.state.led_by, position.players)
        sealed = tuple(position.board.cards(TRAYS.of(seat)) for seat in order)
        if any(len(tray) != ONE_CARD for tray in sealed):
            return ()

        revealed = tuple(tray[SEALED_CARD] for tray in sealed)
        strongest = taken_by(revealed)
        turned: Effects[ShowdownState] = tuple(
            MoveCards(
                source=TRAYS.of(seat),
                indices=frozenset({SEALED_CARD}),
                target=DISCARD,
                face_down=False,
            )
            for seat in order
        )
        closed = self._turn_closed(
            position,
            order[strongest],
            turn_points(revealed, strongest),
        )
        return turned + (SetState(state=closed),)

    def _turn_closed(
        self,
        position: Position[ShowdownState],
        winner: int,
        taken: int,
    ) -> ShowdownState:
        """The cursor the next turn opens on: the tally this one awarded, and every seat still holding cards.

        A round of ten turns runs both holdings out, which leaves nobody to act and the turn number standing at
        the last turn the round played.
        """
        state = position.state
        playing = self._committing(position)
        return state.with_changes(
            round_points=awarded(state.round_points, winner, taken),
            to_act=playing,
            turn_number=state.turn_number + ONE_TURN if playing else state.turn_number,
        )

    def _committing(self, position: Position[ShowdownState]) -> frozenset[int]:
        """The seats with a card left to commit, which either holding may hold."""
        return frozenset(seat for holding in HOLDINGS for seat in position.holding(holding))
