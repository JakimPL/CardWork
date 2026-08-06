from collections.abc import Iterable
from random import Random
from typing import ClassVar, Final

from cardgames.backend.climbing.rules import (
    AWARD,
    CLIMBING_RANKING,
    OPENING_CARD,
    POINTS,
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
from cardwork.rounds.state import BEFORE_THE_FIRST_ROUND, MatchPhase
from cardwork.states.state import NOTHING, Points
from cardwork.zones.zone import Zones
from cardwork.zones.zones import DISCARD, HANDS, STACK

ONE_SEAT: Final[int] = 1


def shown(cards: CardsOrJokers) -> str:
    """The cards of a play as a refusal names them, which is the run they were named in."""
    return " ".join(str(card) for card in cards)


class ClimbingGame(RoundGame[ClimbingState]):
    """A match of rounds in which a combination is answered by a stronger one of as many cards.

    A round deals the deck out in equal shares. The seat on lead puts down any combination this game is played
    by — one card, a pair, a triplet, or five cards reading as a straight, a flush, a full house or a
    straight flush — and every other seat either climbs over it with a stronger combination of as many cards or
    gives its turn up. `rules.CLIMBING_RANKING` holds that vocabulary whole, and `climbs` is the contest itself:
    as many cards, standing higher.

    The round closes on the first seat to play its last card, and every seat is caught with what its hand still
    holds: pips at face value and every court card and ace at ten, added into a standing won at the low end. So
    the match goes to the seat caught with the least over the rounds its table was opened to run.

        game = ClimbingGame(players=4, deck=standard_deck(), conclusion=Conclusion(rounds=3), rng=Random(7))

    **A turn is one of two moves.** A combination played lands face up on the stack and stands there for the next
    seat still answering to climb over, and the one it climbed over goes face down among the cards out of play. So
    the table shows the contest itself, which is the one combination there is to answer. A pass gives that turn up
    for as long as the combination on the table keeps changing hands, and a pass by every seat but one leaves that
    seat's combination unanswered, which hands it the lead again over a bare table.

    **The match opens on the seat holding `rules.OPENING_CARD`**, which is the one card every other card in the
    deck climbs over, and that seat leads a combination holding it. Each round after is led by the seat that went
    out of the one before.
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

        The first round opens with the seat that leads it still to be read off the hands, so the settlement here
        is what names that seat, which is what every driver and adapter beyond this expects of a table it has
        just opened: one seat with a turn to take.

        Args:
            players: how many seats the table holds.
            deck: the cards a round is dealt from, of which every seat takes as many as it divides into.
            conclusion: the clauses the match ends on.
            rng: the generator every shuffle and every seat drawn for a round comes from.
        """
        self._hand_size = len(deck) // players
        self._rejected_cards = len(deck) - self._hand_size * players
        super().__init__(players, deck, conclusion=conclusion, rng=rng)
        self.settle()

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
        A deck dividing unevenly can leave the opening card among them, so the first round of a match is drawn
        again until some seat holds it — one deal in fifty-two at three seats and one in twenty-six at five.
        """
        counts = {
            **HANDS.dealt(self._hand_size, rotation(leader, position.players)),
            DISCARD: self._rejected_cards,
        }
        redeal = Redeal(position, pile=STACK, face_down=True)
        if self._opening_round(position):
            return redeal.admitted(counts, rng, self._deals_the_opening_card)

        return redeal.effects(counts, rng)

    def next_leader(
        self,
        position: Position[ClimbingState],
        rng: Random,
    ) -> int:
        """The seat leading the round about to open, which is the seat that went out of the one before.

        A match opens on the seat holding the opening card, which is read off the hands once they are dealt
        (`advance_round`), so the seat drawn here before the first round is the seat that deal begins at.
        """
        winner = position.state.winner
        if winner is None:
            return super().next_leader(position, rng)

        return winner

    def opening_state(
        self,
        position: Position[ClimbingState],
        leader: int,
    ) -> ClimbingState:
        """The turn a round opens on: a seat on lead, or the search for the seat a match opens on.

        A match opens on the seat holding the opening card, and which seat that is stands in the cards this is
        handed too early to read, since the leader of a round is drawn before its cards go out. So the first
        round opens with nobody to act and the settlement following the deal names the seat (`advance_round`).
        Every round after opens on the seat that went out of the one before, which is the leader handed here.
        """
        opened = position.state.with_changes(
            on_table=None,
            passed=frozenset(),
            winner=None,
        )
        if self._opening_round(position):
            return opened.with_changes(phase=ClimbingPhase.CHOOSING, to_act=frozenset())

        return opened.with_changes(phase=ClimbingPhase.LEAD, to_act=leader)

    def advance_round(
        self,
        position: Position[ClimbingState],
        move: Move | None,
        rng: Random,
    ) -> Effects[ClimbingState]:
        """The seat a dealt match opens on, the round closed on a seat that has played its last card, or nothing.

        A round comes to rest at the boundary that scores it, so the close is owed once: the phase a decided
        round stands in is the answer that it has been written.
        """
        if position.state.phase == ClimbingPhase.CHOOSING:
            return (SetState(state=self._opened(position)),)

        if self.round_over(position):
            return ()

        return self._decided(position)

    def _opening_round(self, position: Position[ClimbingState]) -> bool:
        """Whether the round about to open is the first of the match, which is the one opened from a card."""
        return position.state.round_number == BEFORE_THE_FIRST_ROUND

    def _deals_the_opening_card(self, dealt: Position[ClimbingState]) -> bool:
        """Whether a draw of the deal handed the opening card to a seat rather than setting it aside."""
        return self._holding_the_opening_card(dealt) is not None

    def _holding_the_opening_card(
        self,
        position: Position[ClimbingState],
    ) -> int | None:
        """The seat dealt the opening card, and None where the shares left it lying aside."""
        return next((seat for seat, hand in enumerate(position.held(HANDS)) if OPENING_CARD in hand), None)

    def _opened(self, position: Position[ClimbingState]) -> ClimbingState:
        """The match opened on the seat the deal handed the opening card, which is the seat that leads it.

        Raises:
            LogicError: when no seat holds that card, which the deal of the first round is drawn again until
                one does.
        """
        opener = held(
            self._holding_the_opening_card(position),
            f"seat holds the {OPENING_CARD} this round was dealt to hand out",
        )
        return position.state.with_changes(
            phase=ClimbingPhase.OPENING,
            to_act=opener,
            leader=opener,
        )

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
                return self._played(position, move.player, playing)

    def moves_of(self, position: Position[ClimbingState], seat: int) -> Moves:
        """Every combination one seat may put down, and the pass a seat answering one gives its turn up with.

        A seat on lead offers every combination its hand holds, at each of the counts this game is played by,
        the strongest patterns leading: a hand of thirteen cards lists its straight flushes before its singles.
        A seat answering a combination is held to the count on the table and to climbing over what stands there,
        and the seat opening the match to the combinations of its hand holding the card it opens from.
        """
        match position.state.phase:
            case ClimbingPhase.OPENING:
                return self._opens(position, seat)

            case ClimbingPhase.LEAD:
                return self._leads(position, seat)

            case ClimbingPhase.FOLLOW:
                return self._answers(position, seat)

            case _:
                return ()

    def _opens(self, position: Position[ClimbingState], seat: int) -> Moves:
        """Every combination the seat opening the match may put down, which is each one holding the opening card.

        A single card is a combination this game is played by, so a hand holding that card always holds a
        combination made of it and the seat always has a move.
        """
        hand = position.board.cards(HANDS.of(seat))
        holding = tuple(places for places in CLIMBING_RANKING.selections(hand) if OPENING_CARD in named(hand, places))
        return self._plays(seat, holding)

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
                combination this game is played by, opens the match without the card it opens from, or is made
                in a phase admitting none.
        """
        if play.group != HANDS.name:
            raise IllegalMove(f"Seat {seat} plays out of its {HANDS.name}, and named {play.group!r}")

        cards = self._chosen(position, seat, play.indices)
        combination = CLIMBING_RANKING.exactly(cards)
        if combination is None:
            raise IllegalMove(f"Seat {seat} plays a combination this game is played by, and named {shown(cards)}")

        match position.state.phase:
            case ClimbingPhase.OPENING:
                self._validate_opening(seat, cards)

            case ClimbingPhase.LEAD:
                return

            case ClimbingPhase.FOLLOW:
                self._validate_climb(position, seat, combination)

            case _:
                raise IllegalMove(
                    f"Seat {seat} plays on lead or in answer, and the round stands in the {position.state.phase} phase"
                )

    def _validate_opening(self, seat: int, cards: CardsOrJokers) -> None:
        """Confirm the combination opening the match holds the card the match is opened from.

        Raises:
            IllegalMove: when the cards leave that card out of the combination they read as.
        """
        if OPENING_CARD not in cards:
            raise IllegalMove(
                f"Seat {seat} opens with a combination holding the {OPENING_CARD}, and played {shown(cards)}"
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

    def _swept(self, position: Position[ClimbingState]) -> Effects[ClimbingState]:
        """Whatever the table stands on carried face down out of play, and nothing at all where it stands bare.

        A combination lies on the table for as long as it is the one to climb over, and leaves it the moment
        another lands on it or the contest it stood in closes. So the discard holds everything gone — the cards
        the shares left over and every combination beaten — as a face-down count of what the round has spent.
        """
        standing = position.board.count(STACK)
        if not standing:
            return ()

        return (
            MoveCards(
                source=STACK,
                indices=frozenset(range(standing)),
                target=DISCARD,
                face_down=True,
            ),
        )

    def _played(
        self,
        position: Position[ClimbingState],
        seat: int,
        play: Play,
    ) -> Effects[ClimbingState]:
        """The table swept of what stood on it, the combination laid face up there, and the cursor it leaves."""
        return self._swept(position) + (
            MoveCards(
                source=HANDS.of(seat),
                indices=play.indices,
                target=STACK,
                face_down=False,
            ),
            SetState(state=self._landed(position, seat, play)),
        )

    def _landed(
        self,
        position: Position[ClimbingState],
        seat: int,
        play: Play,
    ) -> ClimbingState:
        """The cursor a landed combination leaves: itself on the table, and the next seat answering it to act.

        The combination is carried as the ranking read it, which is what holds the seat answering to the count
        on the table and to climbing over what stands there. The seats that gave their turn up stay out of the
        contest, which runs on while the combination on the table changes hands.
        """
        return position.state.with_changes(
            phase=ClimbingPhase.FOLLOW,
            to_act=self._next_answering(position, seat, position.state.passed),
            on_table=self._combination(position, seat, play),
        )

    def _combination(
        self,
        position: Position[ClimbingState],
        seat: int,
        play: Play,
    ) -> Combination:
        """The combination a play puts down, as the ranking reads the cards it names.

        Raises:
            LogicError: when the cards read as no combination this game is played by, which every play landing
                here has been held to.
        """
        cards = self._chosen(position, seat, play.indices)
        return held(
            CLIMBING_RANKING.exactly(cards),
            f"combination stands in the cards seat {seat} played",
        )

    def _passed(
        self,
        position: Position[ClimbingState],
        seat: int,
    ) -> Effects[ClimbingState]:
        """The cursor a pass leaves the round on: the turn handed to the next seat still answering, or a fresh lead.

        The turn goes to the next seat round the table yet to pass either way, and where this pass is the last
        one owed, that seat is the one whose combination the rest of the table gave up on. So a contest every
        seat but one has passed over hands its winner the lead, and the combination it settled goes out of play
        with the rest, which leaves that lead standing on a bare table.
        """
        passed = position.state.passed | {seat}
        onwards = self._next_answering(position, seat, passed)
        if len(passed) == position.players - ONE_SEAT:
            return self._swept(position) + (SetState(state=self._reopened(position, onwards)),)

        return (
            SetState(
                state=position.state.with_changes(
                    phase=ClimbingPhase.FOLLOW,
                    to_act=onwards,
                    passed=passed,
                )
            ),
        )

    def _reopened(
        self,
        position: Position[ClimbingState],
        leader: int,
    ) -> ClimbingState:
        """The lead the passes settle, which stands on a bare table as the lead a round opens on does.

        Args:
            position: the table as the pass closing the contest leaves it.
            leader: the seat whose combination the rest of the table passed over, which leads afresh.
        """
        return position.state.with_changes(
            phase=ClimbingPhase.LEAD,
            to_act=leader,
            on_table=None,
            passed=frozenset(),
        )

    def _next_answering(
        self,
        position: Position[ClimbingState],
        seat: int,
        passed: frozenset[int],
    ) -> int:
        """The next seat round the table with a turn to take, which is the first one yet to give its turn up.

        Args:
            position: the table as the turn just taken leaves it.
            seat: the seat that took that turn, which the walk round the table sets out from.
            passed: the seats out of the contest, a seat that has just passed among them.

        Raises:
            LogicError: when every seat has passed, which one contest stops one pass short of.
        """
        return followed(
            seat,
            position.players,
            lambda other: other not in passed,
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
        """The round decided by the seat that played its last card, every other seat caught with what it holds.

        Nobody is left to act and no pass stands, and the round scores the hands as they lie: the seat that went
        out is caught with nothing, and a seat holding cards takes the worth of every one of them.
        """
        return position.state.at_rest(
            ClimbingPhase.DECIDED,
            winner=winner,
            passed=frozenset(),
            round_points=self._caught(position),
        )

    def _caught(self, position: Position[ClimbingState]) -> Points:
        """What each seat is caught holding: the worth of the cards left in its hand, at `POINTS` for every one."""
        return tuple(POINTS.total(position.board.cards(HANDS.of(seat))) for seat in position.seats)
