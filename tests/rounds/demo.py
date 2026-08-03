from enum import StrEnum
from random import Random
from typing import Final

from cardwork.cards.card import Card
from cardwork.cards.points import REGULAR_POINTS
from cardwork.cards.rank import Rank, Ranks
from cardwork.cards.suit import Suit
from cardwork.decks.deck import Deck
from cardwork.decks.decks import does_contain_jokers, to_game_cards
from cardwork.effects.effects import Effects, MoveCards, SetState
from cardwork.exceptions import IllegalMove
from cardwork.games.game import Game
from cardwork.moves.actions import Play
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.rounds.game import RoundGame
from cardwork.rounds.redeal import Redeal
from cardwork.rounds.state import MatchPhase, RoundState
from cardwork.states.state import Points
from cardwork.transactions.transaction import Transaction
from cardwork.zones.presets import HAND, PILE
from cardwork.zones.zone import Zone, ZoneId, Zones

SEATS: Final[int] = 3
HAND_SIZE: Final[int] = 2
ROUNDS: Final[int] = 2
SEED: Final[int] = 20260805
STOCK: Final[ZoneId] = "stock"
DISCARD: Final[ZoneId] = "discard"
FIRST_CARD: Final[int] = 0
RANKS: Final[Ranks] = (Rank.TWO, Rank.THREE, Rank.FOUR)
DECK: Final[Deck] = tuple(Card(rank=rank, suit=suit) for suit in Suit for rank in RANKS)


class TossPhase(StrEnum):
    """The phases a toss round runs in, which is how a game names its own beside the two `MatchPhase` reserves."""

    TOSSING = "tossing"
    COUNTING = "counting"


class MatchState(RoundState):
    """The cursor of a toss match, which records the number of rounds the match was built for.

    Keeping the match length here rather than on the game leaves a replayed position self-describing: how
    many rounds this table was ever going to play is read from the state, as everything else is.
    """

    rounds: int


def hand_of(seat: int) -> ZoneId:
    return f"hand:{seat}"


def tossed(move: Move) -> Play:
    """The play behind a move, which is the one intent this game is built around.

    Raises:
        IllegalMove: when the move carries some other intent.
    """
    if isinstance(move.action, Play):
        return move.action

    raise IllegalMove(f"Seat {move.player} tosses a card, and offered {move.action.kind}")


class TossGame(RoundGame[MatchState]):
    """A match of rounds in which every seat tosses one card face up, in turn from the seat leading the round.

    A seat scores what its card is worth, the round's tally is added into the standing as it closes, the seat
    after its leader takes up the next one, and the match runs the rounds it was built for. This is the round
    layer's exercise rather than a game worth playing: a leader, a turn order, a re-deal between rounds and a
    score that accumulates are the whole of it.
    """

    def __init__(
        self,
        players: int,
        deck: Deck,
        *,
        rounds: int,
        rng: Random | None = None,
    ) -> None:
        self._rounds = rounds
        super().__init__(players, deck, rng=rng)

    def zones(self, players: int, deck: Deck) -> Zones:
        hands = {hand_of(seat): Zone(id=hand_of(seat), owner=seat, visibility=HAND) for seat in range(players)}
        return {
            **hands,
            STOCK: Zone(id=STOCK, visibility=PILE, cards=to_game_cards(deck, face_down=True)),
            DISCARD: Zone(id=DISCARD, visibility=PILE),
        }

    def _validate_players(self, players: int) -> None:
        if not 2 <= players <= 4:
            raise ValueError(f"This game seats 2 to 4 players, and {players} were asked for")

    def _validate_initial_deck(self, deck: Deck) -> None:
        if does_contain_jokers(deck):
            raise ValueError("This game is played with suited cards alone")

    def _initialize(self, players: int) -> MatchState:
        return MatchState(phase=MatchPhase.BETWEEN_ROUNDS, points=(0,) * players, rounds=self._rounds)

    def _final_validation(self, position: Position[MatchState]) -> None:
        short = tuple(
            seat for seat in range(position.players) if len(position.board.zone(hand_of(seat)).cards) != HAND_SIZE
        )
        if short:
            raise ValueError(f"Seats {short} hold a hand of some size other than {HAND_SIZE}")

    def validate(self, position: Position[MatchState], move: Move) -> None:
        indices = tossed(move).indices
        held = len(position.board.zone(hand_of(move.player)).cards)
        if len(indices) != 1:
            raise IllegalMove(f"Seat {move.player} tosses one card at a time, and named {len(indices)}")

        if max(indices) >= held:
            raise IllegalMove(f"Seat {move.player} named position {max(indices)} of a hand holding {held}")

    def expand(self, position: Position[MatchState], move: Move, rng: Random) -> Effects[MatchState]:
        return (
            MoveCards(
                source=hand_of(move.player),
                indices=tossed(move).indices,
                target=DISCARD,
                face_down=False,
            ),
        )

    def deal_round(self, position: Position[MatchState], leader: int, rng: Random) -> Effects[MatchState]:
        counts = {hand_of((leader + place) % position.players): HAND_SIZE for place in range(position.players)}
        return Redeal(position, pile=STOCK, face_down=True).effects(counts, rng)

    def opening_state(self, position: Position[MatchState], leader: int) -> MatchState:
        return position.state.with_changes(phase=TossPhase.TOSSING, to_act=frozenset({leader}))

    def advance_round(
        self,
        position: Position[MatchState],
        move: Move | None,
        rng: Random,
    ) -> Effects[MatchState]:
        """The seat whose turn the round has reached, beside the tally its tossed cards make."""
        state = position.state
        reached = state.with_changes(to_act=self._to_act(position), round_points=self._tally(position))
        return (SetState(state=reached),) if reached != state else ()

    def round_over(self, position: Position[MatchState]) -> bool:
        return len(position.board.zone(DISCARD).cards) >= position.players

    def match_over(self, position: Position[MatchState]) -> bool:
        return position.state.round_number >= position.state.rounds

    def legal_moves(self, position: Position[MatchState]) -> Moves:
        return tuple(
            Move(player=seat, action=Play(group=DISCARD, indices=frozenset({index})))
            for seat in sorted(position.state.to_act)
            for index in range(len(position.board.zone(hand_of(seat)).cards))
        )

    def _to_act(self, position: Position[MatchState]) -> frozenset[int]:
        """The seat whose turn it is, counting on from the leader, and nobody once every seat has tossed."""
        thrown = len(position.board.zone(DISCARD).cards)
        if thrown >= position.players:
            return frozenset()

        return frozenset({(position.state.led_by + thrown) % position.players})

    def _tally(self, position: Position[MatchState]) -> Points:
        """What each seat's tossed card is worth, the discard reading in the order the seats tossed."""
        scored = [0] * position.players
        for place, game_card in enumerate(position.board.zone(DISCARD).cards):
            scored[(position.state.led_by + place) % position.players] = REGULAR_POINTS.of(game_card.card)

        return tuple(scored)


class CountedTossGame(TossGame):
    """A match whose round pauses on a phase of its own, to be counted once every seat has tossed.

    A round of a real game pauses there to reveal what was sealed or to hand a trick to the seat that won it.
    Here the step is the whole of the point: a round that owes something of its own is carried through it by
    settlement, and only then does the boundary close it.
    """

    def advance_round(
        self,
        position: Position[MatchState],
        move: Move | None,
        rng: Random,
    ) -> Effects[MatchState]:
        owed = super().advance_round(position, move, rng)
        if owed or position.state.to_act or position.state.phase == TossPhase.COUNTING:
            return owed

        return (SetState(state=position.state.with_changes(phase=TossPhase.COUNTING)),)

    def round_over(self, position: Position[MatchState]) -> bool:
        return position.state.phase == TossPhase.COUNTING


class WinnerGame(TossGame):
    """A match counting rounds won: the highest tally of a round takes a point, and a tie takes one each."""

    def score_round(self, position: Position[MatchState]) -> Points:
        tally = position.state.round_points
        highest = max(tally)
        return tuple(int(scored == highest) for scored in tally)


class UnscoredGame(TossGame):
    """A match that states no standing before its first round, which the close of that round writes."""

    def _initialize(self, players: int) -> MatchState:
        return MatchState(phase=MatchPhase.BETWEEN_ROUNDS, rounds=self._rounds)


def a_match(rules: type[TossGame], seed: int, rounds: int) -> TossGame:
    """A fresh table of the given rules, seated for three and drawing from a generator of that seed."""
    return rules(players=SEATS, deck=DECK, rounds=rounds, rng=Random(seed))


def toss_a_card(game: Game[MatchState]) -> Transaction[MatchState]:
    """The seat whose turn it is tosses the first card of its hand.

    Raises:
        ValueError: when the turn stands with several seats or with none, which this game never reaches.
    """
    seat = game.state.current
    if seat is None:
        raise ValueError(f"One seat tosses at a time, and the turn stands with {sorted(game.state.to_act)}")

    return game.submit(
        Move(player=seat, action=Play(group=DISCARD, indices=frozenset({FIRST_CARD}))),
        base_seq=game.head,
    )


def toss_the_round(game: Game[MatchState]) -> None:
    """Every seat of the round in play tosses a card, leaving the table for settlement to close."""
    while game.state.to_act:
        toss_a_card(game)
