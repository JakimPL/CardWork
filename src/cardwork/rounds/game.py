from abc import ABC, abstractmethod
from random import Random

from cardwork.decks.deck import Deck
from cardwork.effects.effects import Effects, SetState
from cardwork.games.game import Game
from cardwork.moves.move import Move
from cardwork.positions.position import Position
from cardwork.rounds.conclusion import Conclusion
from cardwork.rounds.state import MatchPhase, RoundStateT
from cardwork.states.state import NOTHING, Points


def standing(position: Position[RoundStateT]) -> Points:
    """The score of record as it stands, which reads as a tally of nothing at a table yet to score a round."""
    points = position.state.points
    return points if points is not None else (NOTHING,) * position.players


class RoundGame(Game[RoundStateT], ABC):
    """A match played as a series of rounds: each dealt afresh, led by a seat in turn, scored as it closes.

    A game states what one round is — the cards it deals, the cursor it opens on, what happens inside it and
    when it has run out — and this layer sequences the match around that. The first round opens as the table
    is built, a finished round is scored into the standing, the seat after its leader takes up the next one,
    and the match closes once the standing meets the `Conclusion` the table was opened with.

    Writing one is answering these:

    | hook | states |
    |---|---|
    | `initial_state(players)` | the cursor the table opens on, before a card has moved |
    | `deal_round(position, leader, rng)` | the cards a fresh round is dealt, for which `Redeal` is the usual answer |
    | `opening_state(position, leader)` | the cursor a round opens on: the phase it runs in, and who acts |
    | `advance_round(position, move, rng)` | what the rules owe inside a round, exactly as `advance` states it |
    | `round_over(position)` | whether the round in play has run out |

    `next_leader`, `score_round` and `match_over` arrive with the answer most matches want, so a game that seats
    its rounds by the standing, awards a match point to the winner of each round, or ends on something the
    standing cannot state overrides one of those three.

    `MatchPhase` holds the two phases this layer runs in, and every phase beside those two says a round is in play,
    which leaves a game free to name its own. A table opens between rounds, and the clauses it runs to are stamped
    onto the cursor it states:

        def initial_state(self, players: int) -> ShowdownState:
            return ShowdownState(phase=MatchPhase.BETWEEN_ROUNDS, points=(0,) * players, award=AWARD)
    """

    def __init__(
        self,
        players: int,
        deck: Deck,
        *,
        conclusion: Conclusion,
        rng: Random | None = None,
    ) -> None:
        """A table seated for that many players, dealing from that deck, running to that conclusion.

        Args:
            players: how many seats the table holds.
            deck: the cards the table is dealt from, which the game's own validation reads.
            conclusion: the clauses the match ends on, stamped onto the cursor the table opens on so that a
                position describes the ending it was running to wherever it is read.
            rng: the generator every shuffle and every seat drawn for a round comes from.
        """
        self._conclusion = conclusion
        super().__init__(players, deck, rng=rng)

    def _initialize(self, players: int) -> RoundStateT:
        """The cursor the table opens on, carrying the clauses the match runs to.

        A game states the rest of it as `initial_state`, and the conclusion is stamped over that here, so a game
        writes the phase and the tally its table opens with and names its ending in one place only: the conclusion
        the table was opened with.
        """
        return self.initial_state(players).with_changes(**dict(self._conclusion))

    def advance(
        self,
        position: Position[RoundStateT],
        move: Move | None,
        rng: Random,
    ) -> Effects[RoundStateT]:
        """The round's own bookkeeping behind a move, and the boundaries of the match while the table settles.

        A move is answered by `advance_round` alone, which keeps the scoring of a round and the deal of the
        next out of the transaction one seat's move commits. Both belong to the settlement that follows it,
        where this reads the round as it stands: what it still owes, whether it has run out, and whether the
        match it closes is decided.
        """
        if move is not None:
            return self.advance_round(position, move, rng)

        return self._settling(position, rng)

    def _settling(
        self,
        position: Position[RoundStateT],
        rng: Random,
    ) -> Effects[RoundStateT]:
        """What the rules owe with no seat behind the question, which is one of the three the phase stands in."""
        match position.state.phase:
            case MatchPhase.MATCH_OVER:
                return ()

            case MatchPhase.BETWEEN_ROUNDS:
                return self.finish_match(position) if self.match_over(position) else self.open_round(position, rng)

            case _:
                return self._within_round(position, rng)

    def _within_round(
        self,
        position: Position[RoundStateT],
        rng: Random,
    ) -> Effects[RoundStateT]:
        """What the round in play still owes, and its close once it owes nothing and has run out."""
        owed = self.advance_round(position, None, rng)
        if owed:
            return owed

        return self.close_round(position) if self.round_over(position) else ()

    def open_round(
        self,
        position: Position[RoundStateT],
        rng: Random,
    ) -> Effects[RoundStateT]:
        """The effects opening the next round: the cards it is dealt, and the cursor it begins on.

        The round's count, its leader and a tally of zeros are stamped onto the cursor the game states, so a
        game writes the phase its round runs in and reads the rest back from the state. The leader is drawn
        before the cards go out, which is what lets a deal begin at the seat leading the round.
        """
        leader = self.next_leader(position, rng)
        opened = self.opening_state(position, leader).with_changes(
            round_number=position.state.round_number + 1,
            leader=leader,
            round_points=(0,) * position.players,
        )
        return self.deal_round(position, leader, rng) + (SetState(state=opened),)

    def close_round(self, position: Position[RoundStateT]) -> Effects[RoundStateT]:
        """The effects closing the round in play: its award added into the standing, and the table left between rounds.

        The round's own tally stays as it stands, so the transaction that closes a round reports what it scored
        and the one that opens the next clears it.
        """
        state = position.state
        closed = state.at_rest(
            MatchPhase.BETWEEN_ROUNDS,
            points=tuple(
                before + won
                for before, won in zip(
                    standing(position),
                    self.score_round(position),
                    strict=True,
                )
            ),
        )
        return (SetState(state=closed),)

    def finish_match(
        self,
        position: Position[RoundStateT],
    ) -> Effects[RoundStateT]:
        """The effects closing the match: the phase every seat reads as over, and nobody left to act."""
        return (SetState(state=position.state.at_rest(MatchPhase.MATCH_OVER)),)

    def next_leader(
        self,
        position: Position[RoundStateT],
        rng: Random,
    ) -> int:
        """The seat to lead the round about to open: one drawn at random before the first, the next seat after.

        The draw lands in the journal inside the `SetState` that opens the round, so a replay seats the same
        leader. A game that seats its rounds otherwise — the seat that won the last one, the seat trailing the
        standing — states that here.
        """
        led = position.state.leader
        if led is None:
            return rng.randrange(position.players)

        return (led + 1) % position.players

    def match_over(self, position: Position[RoundStateT]) -> bool:
        """Whether the standing has decided the match, which the clauses the cursor carries answer.

        Asked between rounds with the round that just closed already scored, so the standing read here is the one
        that round was added into and a match ends at a boundary with every round played out. A game whose match
        ends on something a standing cannot state — a seat left holding every card, a contract made — states that
        here instead.
        """
        return position.state.concluded(standing(position))

    def score_round(
        self,
        position: Position[RoundStateT],
    ) -> Points:
        """What the round in play awards each seat, which is the tally it kept.

        A match that awards a point to the winner of each round converts here, reading the tally to find the
        seat the round belongs to and awarding that seat alone.
        """
        return position.state.round_points

    def _deal_cards(  # pylint: disable=unused-argument
        self,
        position: Position[RoundStateT],
        rng: Random,
    ) -> Effects[RoundStateT]:
        """The cards lie where `zones` laid them, since the first deal is the first round's own."""
        return ()

    @abstractmethod
    def initial_state(self, players: int) -> RoundStateT:
        """The cursor the table opens on: the phase it stands in, its tally of nothing, and the end it is won at.

        A table opens between rounds, since the first round is the first boundary, and the clauses the match runs
        to are stamped over whatever this states.

        Args:
            players: how many seats the table holds, which is the width of the standing it opens with.
        """

    @abstractmethod
    def deal_round(
        self,
        position: Position[RoundStateT],
        leader: int,
        rng: Random,
    ) -> Effects[RoundStateT]:
        """The cards a fresh round is dealt, gathered from wherever the last one left them.

        `Redeal` is the usual answer: everything back to one pile, shuffled, and dealt out by the count each
        zone is owed.

        Args:
            position: the table as the round about to open finds it, its cards lying where the last left them.
            leader: the seat leading the round, which is where a deal round the table begins and which reads
                the extra card a game gives the seat it opens on.
            rng: the generator the shuffle draws from, whose draw travels as the `Reorder` it decides.
        """

    @abstractmethod
    def opening_state(
        self,
        position: Position[RoundStateT],
        leader: int,
    ) -> RoundStateT:
        """The cursor a fresh round begins on: the phase it runs in, and the seats that owe an action.

        Args:
            position: the table as the round about to open finds it, its cards yet to be dealt.
            leader: the seat leading the round, which is what a game reads to set the first turn.
        """

    @abstractmethod
    def advance_round(
        self,
        position: Position[RoundStateT],
        move: Move | None,
        rng: Random,
    ) -> Effects[RoundStateT]:
        """What the rules owe inside the round in play, which `advance` states in full.

        Answer with an empty run once the round owes nothing, since that is what hands the table on to
        `round_over` and the boundary beyond it.
        """

    @abstractmethod
    def round_over(self, position: Position[RoundStateT]) -> bool:
        """Whether the round in play has run out, asked once it owes nothing further."""
