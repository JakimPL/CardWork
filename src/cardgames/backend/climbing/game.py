from random import Random
from typing import ClassVar

from cardgames.backend.climbing.rules import (
    SEATS_LEAST,
    SEATS_MOST,
    can_beat,
    combination_of,
)
from cardgames.backend.climbing.state import ClimbingPhase, ClimbingState
from cardgames.backend.climbing.zones import climbing_zones
from cardwork.cards.card import Cards
from cardwork.cards.game import suited
from cardwork.combinations.combination import Combination
from cardwork.decks.deck import Deck
from cardwork.decks.standard import is_standard_deck
from cardwork.effects.effects import Effects, MoveCards, SetState
from cardwork.exceptions import (
    GameValidationError,
    IllegalMove,
    LogicError,
)
from cardwork.games.intents import Intents
from cardwork.moves.actions import Pass, Play
from cardwork.moves.move import Move
from cardwork.positions.position import Position
from cardwork.rounds.conclusion import Conclusion
from cardwork.rounds.game import NOTHING, RoundGame
from cardwork.rounds.redeal import Redeal
from cardwork.rounds.seating import rotation
from cardwork.zones.zone import Zones, cards_of
from cardwork.zones.zones import DISCARD, STACK, hand_of


class ClimbingGame(RoundGame[ClimbingState]):
    intents: ClassVar[Intents[Pass | Play]] = Intents(Pass, Play)

    def __init__(
        self,
        players: int,
        deck: Deck,
        *,
        conclusion: Conclusion,
        rng: Random | None = None,
    ) -> None:
        self._hand_size = len(deck) // players
        self._rejected_cards = len(deck) - self._hand_size * players
        super().__init__(players, deck, conclusion=conclusion, rng=rng)

    def zones(self, players: int, deck: Deck) -> Zones:
        return climbing_zones(players)

    def _validate_players(self, players: int) -> None:
        if not SEATS_LEAST <= players <= SEATS_MOST:
            raise GameValidationError(
                f"This game seats {SEATS_LEAST} to {SEATS_MOST} players, and {players} were asked for"
            )

    def _validate_initial_deck(self, deck: Deck) -> None:
        if not is_standard_deck(deck):
            raise GameValidationError("This game is played with one standard deck of suited cards")

    def initial_state(self, players: int) -> ClimbingState:
        return ClimbingState(
            phase=ClimbingPhase.LEAD,
            points=(NOTHING,) * players,
        )

    def _final_validation(self, position: Position[ClimbingState]) -> None:
        """Confirm the deal left every seat the four cards it is dealt, which its draws then build on.

        Raises:
            GameValidationError: when a hand holds a number of cards other than the deal gives it.
        """
        short = tuple(
            seat for seat in range(position.players) if len(position.board.zone(hand_of(seat)).cards) != self._hand_size
        )
        if short:
            raise GameValidationError(
                f"Seats {short} hold a hand of a size other than the {self._hand_size} the deal gives them"
            )

        discarded = len(position.board.zone(DISCARD).cards)
        if discarded != self._rejected_cards:
            raise GameValidationError(
                f"The deal left {discarded} cards in the discard, but {self._rejected_cards} were rejected"
            )

    def deal_round(
        self,
        position: Position[ClimbingState],
        leader: int,
        rng: Random,
    ) -> Effects[ClimbingState]:
        counts = {
            **{hand_of(seat): self._hand_size for seat in rotation(leader, position.players)},
            DISCARD: self._rejected_cards,
        }
        redeal = Redeal(position, pile=STACK, face_down=True)
        return redeal.effects(counts, rng)

    def opening_state(
        self,
        position: Position[ClimbingState],
        leader: int,
    ) -> ClimbingState:
        """The first turn of the round, which every seat owes a commitment to at once."""
        return position.state.with_changes(
            phase=ClimbingPhase.LEAD,
            to_act=leader,
            winner=None,
        )

    def advance_round(
        self,
        position: Position[ClimbingState],
        move: Move | None,
        rng: Random,
    ) -> Effects[ClimbingState]:
        decided = self._decided(position)
        return decided

    def round_over(self, position: Position[ClimbingState]) -> bool:
        return position.state.phase == ClimbingPhase.DECIDED

    def validate(self, position: Position[ClimbingState], move: Move) -> None:
        """
        Raises:
            IllegalMove: when the move carries another intent, or breaks a rule of the intent it carries.
        """
        match self.intents.read(move):
            case Pass():
                self._validate_pass(position, move.player)

            case Play() as playing:
                self._validate_play(position, move.player, playing)

    def expand(
        self,
        position: Position[ClimbingState],
        move: Move,
        rng: Random,
    ) -> Effects[ClimbingState]:
        match self.intents.read(move):
            case Pass():
                return self._passed(position, move.player)

            case Play() as playing:
                return self._played(move.player, playing)

    def _validate_pass(
        self,
        position: Position[ClimbingState],
        seat: int,
    ) -> None:
        """Confirm a pass is legal, which is that it is made in the right phase and by a seat that has not passed.

        Raises:
            IllegalMove: when the pass is made in the wrong phase, or by a seat that has already passed.
        """
        if position.state.phase != ClimbingPhase.FOLLOW:
            raise IllegalMove(f"Seat {seat} cannot pass in the {position.state.phase} phase")

        if seat in position.state.passed:
            raise IllegalMove(f"Seat {seat} cannot pass again after it has already passed")

    def _validate_play(
        self,
        position: Position[ClimbingState],
        seat: int,
        play: Play,
    ) -> None:
        """Confirm a play is legal, which is that it is made in the right phase and with the right cards.

        Raises:
            IllegalMove: when the play is made in the wrong phase, or with cards the seat does not hold.
        """
        if play.group != DISCARD:
            raise IllegalMove(f"Seat {seat} can only play to the discard, not to {play.group}")

        if position.state.phase == ClimbingPhase.LEAD:
            return

        if position.state.phase != ClimbingPhase.FOLLOW:
            raise IllegalMove(f"Seat {seat} cannot play in the {position.state.phase} phase")

        size = position.state.combination_size
        cards = tuple(card for index, card in enumerate(self._held_by(position, seat)) if index in play.indices)
        combination = combination_of(cards)
        if len(play.indices) != size:
            raise IllegalMove(
                f"Seat {seat} cannot play in the {position.state.phase} phase with a combination "
                f"of size {len(cards)} instead of {size}"
            )

        previous_combination = self._previous_combination(position)
        if not can_beat(combination, previous_combination):
            raise IllegalMove(
                f"Seat {seat} cannot play in the {position.state.phase} phase with a combination "
                f"of {cards} that does not beat {combination.cards}"
            )

    def _passed(
        self,
        position: Position[ClimbingState],
        seat: int,
    ) -> Effects[ClimbingState]:
        passed: Effects[ClimbingState]
        if len(self.position.state.passed) == self.players - 1:
            passed = (
                SetState(
                    state=position.state.with_changes(
                        phase=ClimbingPhase.LEAD,
                        to_act=seat,
                        passed=frozenset(),
                    )
                ),
            )
        else:
            passed = (
                SetState(
                    state=position.state.with_changes(
                        phase=ClimbingPhase.FOLLOW,
                        to_act=self._next_to_follow(position, seat),
                        passed=position.state.passed | {seat},
                    )
                ),
            )
        return passed

    def _played(
        self,
        seat: int,
        play: Play,
    ) -> Effects[ClimbingState]:
        """The effects of a seat playing, which is that the cards are moved to the discard and the next phase is set.

        Raises:
            IllegalMove: when the play is made in the wrong phase, or with cards the seat does not hold.
        """
        moved: Effects[ClimbingState] = (
            MoveCards(
                source=hand_of(seat),
                indices=play.indices,
                target=STACK,
                face_down=False,
            ),
        )
        return moved

    def _decided(
        self,
        position: Position[ClimbingState],
    ) -> Effects[ClimbingState]:
        if not any(not self._held_by(position, seat) for seat in range(self.players)):
            return ()

        decided: Effects[ClimbingState] = (
            SetState(
                state=position.state.with_changes(
                    phase=ClimbingPhase.DECIDED,
                    to_act=frozenset(),
                    passed=frozenset(),
                )
            ),
        )
        return decided

    def _won_by(
        self,
        position: Position[ClimbingState],
        winner: int,
    ) -> ClimbingState:
        """The state of the round after a seat has won, which is that it is set as the winner and the phase is decided."""
        return position.state.with_changes(
            phase=ClimbingPhase.DECIDED,
            winner=winner,
        )

    def _next_to_follow(
        self,
        position: Position[ClimbingState],
        seat: int,
    ) -> int:
        """The seats that have not passed, minus the one that has just acted."""
        for _ in range(position.players):
            seat = (seat + 1) % position.players
            if seat not in position.state.passed:
                return seat

        raise LogicError(f"Seat {seat} acted when all seats have already passed, which is {position.state.passed}")

    def _previous_combination(
        self,
        position: Position[ClimbingState],
    ) -> Combination:
        size = position.state.combination_size
        if not size:
            raise LogicError("")

        cards = self._on_stack(position)
        if len(cards) != size:
            raise LogicError("")

        return combination_of(cards)

    def _on_stack(self, position: Position[ClimbingState]) -> Cards:
        if not position.state.combination_size:
            return ()

        return suited(position.board.zone(STACK).cards[-position.state.combination_size :])

    def _held_by(
        self,
        position: Position[ClimbingState],
        seat: int,
    ) -> Cards:
        """The cards one seat holds, as the rules read them."""
        return suited(cards_of(position.board.zone(hand_of(seat))))
