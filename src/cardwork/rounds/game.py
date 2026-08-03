from abc import ABC, abstractmethod
from random import Random

from cardwork.effects.effects import Effects, SetState
from cardwork.games.game import Game
from cardwork.moves.move import Move
from cardwork.positions.position import Position
from cardwork.rounds.state import MatchPhase, RoundStateT
from cardwork.states.state import Points


class RoundGame(Game[RoundStateT], ABC):
    """A match played as a series of rounds: each dealt afresh, led by a seat in turn, scored as it closes.

    A game states what one round is — the cards it deals, the cursor it opens on, what happens inside it and
    when it has run out — and this layer sequences the match around that. The first round opens as the table
    is built, a finished round is scored into the standing, the seat after its leader takes up the next one,
    and the match closes once the game calls the standing decided.

    Writing one is answering these:

    | hook | states |
    |---|---|
    | `deal_round(position, leader, rng)` | the cards a fresh round is dealt, for which `Redeal` is the usual answer |
    | `opening_state(position, leader)` | the cursor a round opens on: the phase it runs in, and who acts |
    | `advance_round(position, move, rng)` | what the rules owe inside a round, exactly as `advance` states it |
    | `round_over(position)` | whether the round in play has run out |
    | `match_over(position)` | whether the standing has decided the match |

    `next_leader` and `score_round` arrive with the answer most matches want, so a game that seats its rounds
    by the standing, or awards a match point to the winner of each round, overrides one of those two.

    `MatchPhase` holds the two phases this layer runs in, and every phase beside those two says a round is in play,
    which leaves a game free to name its own. A table opens between rounds:

        def _initialize(self, players: int) -> ShowdownState:
            return ShowdownState(phase=MatchPhase.BETWEEN_ROUNDS, points=(0,) * players, rounds=self._rounds)
    """

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
        standing = state.points if state.points is not None else (0,) * position.players
        closed = state.with_changes(
            phase=MatchPhase.BETWEEN_ROUNDS,
            to_act=frozenset(),
            points=tuple(
                before + won
                for before, won in zip(
                    standing,
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
        finished = position.state.with_changes(phase=MatchPhase.MATCH_OVER, to_act=frozenset())
        return (SetState(state=finished),)

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

    @abstractmethod
    def match_over(self, position: Position[RoundStateT]) -> bool:
        """Whether the standing has decided the match, asked between rounds with every round scored."""
