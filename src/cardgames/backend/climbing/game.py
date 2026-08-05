from collections.abc import Iterable
from random import Random
from typing import ClassVar, Final

from cardgames.backend.climbing.rules import (
    AWARD,
    CLIMBING_RANKING,
    SEATS_LEAST,
    SEATS_MOST,
)
from cardgames.backend.climbing.state import ClimbingPhase, ClimbingState
from cardgames.backend.climbing.zones import climbing_zones
from cardwork.cards.game import CardsOrJokers
from cardwork.combinations.combination import Combination
from cardwork.combinations.selection import Selection
from cardwork.decks.deck import Deck, Indices
from cardwork.decks.decks import named
from cardwork.decks.standard import confirm_standard_deck
from cardwork.effects.effects import Effects, MoveCards, SetState
from cardwork.exceptions import GameValidationError, IllegalMove
from cardwork.games.capacity import Capacity
from cardwork.games.dealt import confirm_dealt
from cardwork.games.intents import Intents
from cardwork.models.held import held
from cardwork.moves.actions import Pass, Play
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.rounds.conclusion import Conclusion
from cardwork.rounds.game import RoundGame
from cardwork.rounds.redeal import Redeal
from cardwork.rounds.seating import followed, rotation
from cardwork.rounds.state import MatchPhase
from cardwork.states.state import NOTHING
from cardwork.zones.zone import Zones
from cardwork.zones.zones import DISCARD, HANDS, STACK

ONE_SEAT: Final[int] = 1


class ClimbingGame(RoundGame[ClimbingState]):
    """A match of rounds in which a combination is answered by a stronger one of as many cards.

    A round deals the deck out in equal shares. The seat on lead puts down any combination this game is played
    by — one card, a pair, a triplet, or five cards reading as a straight, a flush, a full house or a
    straight flush — and every other seat either climbs over it with a stronger combination of as many cards or
    gives its turn up. `rules.CLIMBING_RANKING` holds that vocabulary whole, and `climbs` is the contest itself:
    as many cards, standing higher.

    The round goes to the first seat to play its last card, and the match runs to the conclusion its table was
    opened with.

        game = ClimbingGame(players=4, deck=standard_deck(), conclusion=Conclusion(rounds=3), rng=Random(7))

    **What a round still owes is its turn.** A play moves its cards onto the stack and a pass hands the turn to
    the next seat still answering; the cursor a landed combination leaves behind — the seat that answers it, and
    the lead the passes settle — is the work left to write.
    """

    capacity: ClassVar[Capacity] = Capacity(least=SEATS_LEAST, most=SEATS_MOST)
    intents: ClassVar[Intents[Pass | Play]] = Intents(Pass, Play)

    def __init__(
        self,
        players: int,
        deck: Deck,
        *,
        conclusion: Conclusion,
        rng: Random | None = None,
    ) -> None:
        """A table whose seats take equal shares of the deck, the cards those leave over lying aside.

        Args:
            players: how many seats the table holds.
            deck: the cards a round is dealt from, of which every seat takes as many as it divides into.
            conclusion: the clauses the match ends on.
            rng: the generator every shuffle and every seat drawn for a round comes from.
        """
        self._hand_size = len(deck) // players
        self._rejected_cards = len(deck) - self._hand_size * players
        super().__init__(players, deck, conclusion=conclusion, rng=rng)

    def zones(self, players: int, deck: Deck) -> Zones:
        return climbing_zones(players, deck)

    def _validate_initial_deck(self, deck: Deck) -> None:
        confirm_standard_deck(deck)

    def initial_state(self, players: int) -> ClimbingState:
        return ClimbingState(
            phase=MatchPhase.BETWEEN_ROUNDS,
            points=(NOTHING,) * players,
            award=AWARD,
        )

    def _final_validation(self, position: Position[ClimbingState]) -> None:
        """Confirm the deal left every seat its share of the deck, with the cards over it lying aside.

        Raises:
            GameValidationError: when a hand holds a count other than the share the deal gives it, or when the
                cards set aside are other than the share leaves over.
        """
        confirm_dealt(position, HANDS, self._hand_size)

        aside = position.board.count(DISCARD)
        if aside != self._rejected_cards:
            raise GameValidationError(
                f"The deal set {aside} cards aside, and equal shares of this deck leave {self._rejected_cards}"
            )

    def deal_round(
        self,
        position: Position[ClimbingState],
        leader: int,
        rng: Random,
    ) -> Effects[ClimbingState]:
        """Every card gathered and shuffled, then an equal share dealt to each seat from the leader onwards.

        What the shares leave over goes to the discard, which is where a round keeps the cards nobody was dealt.
        """
        counts = {
            **HANDS.dealt(self._hand_size, rotation(leader, position.players)),
            DISCARD: self._rejected_cards,
        }
        return Redeal(position, pile=STACK, face_down=True).effects(counts, rng)

    def opening_state(
        self,
        position: Position[ClimbingState],
        leader: int,
    ) -> ClimbingState:
        """The turn a round opens on, which is the seat on lead with the table standing on nothing yet."""
        return position.state.with_changes(
            phase=ClimbingPhase.LEAD,
            to_act=leader,
            on_table=None,
            passed=frozenset(),
            winner=None,
        )

    def advance_round(
        self,
        position: Position[ClimbingState],
        move: Move | None,
        rng: Random,
    ) -> Effects[ClimbingState]:
        """The round closed on the seat that has played its last card, which is what a landed play may leave."""
        return self._decided(position)

    def round_over(self, position: Position[ClimbingState]) -> bool:
        return position.state.phase == ClimbingPhase.DECIDED

    def validate(self, position: Position[ClimbingState], move: Move) -> None:
        """Read the move as one of the two a turn is made of, and hold it to the rules of that one.

        Raises:
            IllegalMove: when the move breaks a rule of the intent it carries.
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
        """The cards a turn moves, which is the combination it lays on the stack, and the turn a pass hands on."""
        match self.intents.read(move):
            case Pass():
                return self._passed(position, move.player)

            case Play() as playing:
                return self._played(move.player, playing)

    def moves_of(self, position: Position[ClimbingState], seat: int) -> Moves:
        """Every combination one seat may put down, and the pass a seat answering one gives its turn up with.

        A seat on lead offers every combination its hand holds, at each of the counts this game is played by,
        the strongest patterns leading: a hand of thirteen cards lists its straight flushes before its singles.
        A seat answering a combination is held to the count on the table and to climbing over what stands there.
        """
        match position.state.phase:
            case ClimbingPhase.LEAD:
                return self._leads(position, seat)

            case ClimbingPhase.FOLLOW:
                return self._answers(position, seat)

            case _:
                return ()

    def _leads(self, position: Position[ClimbingState], seat: int) -> Moves:
        """Every combination the seat on lead may put down, which is every one its hand holds."""
        return self._plays(seat, CLIMBING_RANKING.selections(position.board.cards(HANDS.of(seat))))

    def _answers(self, position: Position[ClimbingState], seat: int) -> Moves:
        """Every combination one seat may climb over the table with, beside the pass it may give instead.

        The ranking narrowed to the count on the table is what a hand is read against, so a seat answering a
        pair is offered its pairs alone, and of those the ones standing higher than the pair it answers.

        Raises:
            LogicError: when the round stands in answer with no combination on the table.
        """
        on_table = held(position.state.on_table, f"combination stands on the table for seat {seat} to answer")
        hand = position.board.cards(HANDS.of(seat))
        answering = CLIMBING_RANKING.sized(on_table.pattern.size)
        climbing = tuple(places for places in answering.selections(hand) if self._climbs(named(hand, places), on_table))
        return self._plays(seat, climbing) + (Move(player=seat, action=Pass()),)

    def _plays(self, seat: int, combinations: Iterable[Selection]) -> Moves:
        """One move for each set of places, every one of them a combination out of the seat's own hand."""
        return tuple(Move(player=seat, action=Play(group=HANDS.name, indices=places)) for places in combinations)

    def _climbs(self, cards: CardsOrJokers, on_table: Combination) -> bool:
        """Whether the cards read as a combination standing above the one the table holds."""
        combination = CLIMBING_RANKING.exactly(cards)
        return combination is not None and CLIMBING_RANKING.climbs(combination, on_table)

    def _validate_pass(
        self,
        position: Position[ClimbingState],
        seat: int,
    ) -> None:
        """Confirm the pass answers a combination on the table, from a seat that has yet to pass over it.

        Raises:
            IllegalMove: when the round stands on no combination to pass over, or when the seat has already
                given its turn up over the one it stands on.
        """
        if position.state.phase != ClimbingPhase.FOLLOW:
            raise IllegalMove(
                f"Seat {seat} passes over a combination on the table, "
                f"and the round stands in the {position.state.phase} phase"
            )

        if seat in position.state.passed:
            raise IllegalMove(f"Seat {seat} passes once over a combination, and has passed over this one")

    def _validate_play(
        self,
        position: Position[ClimbingState],
        seat: int,
        play: Play,
    ) -> None:
        """Confirm the play is a combination out of the seat's own hand, standing where the round admits one.

        Raises:
            IllegalMove: when the play names another group, names a position beyond the hand, reads as no
                combination this game is played by, or is made in a phase admitting none.
        """
        if play.group != HANDS.name:
            raise IllegalMove(f"Seat {seat} plays out of its {HANDS.name}, and named {play.group!r}")

        cards = self._chosen(position, seat, play.indices)
        combination = CLIMBING_RANKING.exactly(cards)
        if combination is None:
            shown = " ".join(str(card) for card in cards)
            raise IllegalMove(f"Seat {seat} plays a combination this game is played by, and named {shown}")

        match position.state.phase:
            case ClimbingPhase.LEAD:
                return

            case ClimbingPhase.FOLLOW:
                self._validate_climb(position, seat, combination)

            case _:
                raise IllegalMove(
                    f"Seat {seat} plays on lead or in answer, and the round stands in the {position.state.phase} phase"
                )

    def _validate_climb(
        self,
        position: Position[ClimbingState],
        seat: int,
        combination: Combination,
    ) -> None:
        """Confirm the combination takes as many cards as the one on the table and stands above it.

        Raises:
            IllegalMove: when the combination stands no higher than the one on the table, or takes another
                count of cards, which is a contest it stands beside rather than over.
            LogicError: when the round stands in answer with no combination on the table.
        """
        on_table = held(position.state.on_table, f"combination stands on the table for seat {seat} to climb over")
        if not CLIMBING_RANKING.climbs(combination, on_table):
            raise IllegalMove(f"Seat {seat} climbs over {on_table}, and played {combination}")

    def _chosen(
        self,
        position: Position[ClimbingState],
        seat: int,
        places: Indices,
    ) -> CardsOrJokers:
        """The cards the places name out of the seat's own hand, in the run the hand holds them in.

        Raises:
            IllegalMove: when a place lies past the cards the hand holds.
        """
        size = position.board.count(HANDS.of(seat))
        if max(places) >= size:
            raise IllegalMove(f"Seat {seat} named position {max(places)} of a hand holding {size}")

        return position.board.taken(HANDS.of(seat), places)

    def _played(self, seat: int, play: Play) -> Effects[ClimbingState]:
        """The combination laid face up on the stack, where the whole table reads what it stands to climb over."""
        return (
            MoveCards(
                source=HANDS.of(seat),
                indices=play.indices,
                target=STACK,
                face_down=False,
            ),
        )

    def _passed(
        self,
        position: Position[ClimbingState],
        seat: int,
    ) -> Effects[ClimbingState]:
        """The cursor a pass leaves the round on: the turn handed to the next seat still answering, or a fresh lead.

        A pass by the last seat still answering leaves the combination on the table unanswered, which opens the
        lead again with every pass cleared.
        """
        if len(position.state.passed) == position.players - ONE_SEAT:
            return (
                SetState(
                    state=position.state.with_changes(
                        phase=ClimbingPhase.LEAD,
                        to_act=seat,
                        passed=frozenset(),
                    )
                ),
            )

        return (
            SetState(
                state=position.state.with_changes(
                    phase=ClimbingPhase.FOLLOW,
                    to_act=self._next_answering(position, seat),
                    passed=position.state.passed | {seat},
                )
            ),
        )

    def _next_answering(
        self,
        position: Position[ClimbingState],
        seat: int,
    ) -> int:
        """The next seat round the table still answering the combination on the table.

        Raises:
            LogicError: when every seat has passed, which a pass leaving one seat to answer never reaches.
        """
        return followed(
            seat,
            position.players,
            lambda other: other not in position.state.passed,
            including=False,
        )

    def _decided(self, position: Position[ClimbingState]) -> Effects[ClimbingState]:
        """The round closed on the seat holding no card, and nothing at all while every seat still holds one."""
        gone_out = self._gone_out(position)
        if gone_out is None:
            return ()

        return (SetState(state=self._won_by(position, gone_out)),)

    def _gone_out(self, position: Position[ClimbingState]) -> int | None:
        """The seat that has played its last card, and None while every seat still holds one.

        The seats holding a card in hand are the reading this stands on. A hand empties on its owner's own play,
        so the seat named here is the one whose play closed the round.
        """
        emptied = frozenset(position.seats) - position.holding(HANDS)
        return min(emptied) if emptied else None

    def _won_by(
        self,
        position: Position[ClimbingState],
        winner: int,
    ) -> ClimbingState:
        """The round decided by the seat that played its last card, which leaves nobody to act and no pass standing."""
        return position.state.at_rest(
            ClimbingPhase.DECIDED,
            winner=winner,
            passed=frozenset(),
        )
