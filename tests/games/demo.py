from random import Random
from typing import ClassVar, Final

from cardwork.cards.card import Card
from cardwork.cards.rank import Rank
from cardwork.cards.suit import Suit
from cardwork.decks.deck import Deck
from cardwork.decks.decks import does_contain_jokers, to_game_cards
from cardwork.decks.draw import permutation
from cardwork.effects.effects import Effects, MoveCards, Reorder, SetState
from cardwork.exceptions import GameValidationError, IllegalMove
from cardwork.games.game import Game
from cardwork.games.intents import Intents
from cardwork.moves.actions import Play, Take
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.states.state import GameState, Points
from cardwork.zones.presets import HAND, PILE
from cardwork.zones.zone import Zone, ZoneId, Zones
from cardwork.zones.zones import discard, hand_of, hands

SEATS: Final[int] = 3
HAND_SIZE: Final[int] = 3
RANKS: Final[tuple[Rank, ...]] = (Rank.ACE, Rank.KING, Rank.QUEEN)
DECK: Final[Deck] = tuple(Card(rank=rank, suit=suit) for suit in Suit for rank in RANKS)
LAYING: Final[Intents[Play]] = Intents(Play)
LAYING_OR_RETRACTING: Final[Intents[Play | Take]] = Intents(Play, Take)


def tray_of(seat: int) -> ZoneId:
    return f"sealed:{seat}"


class DiscardGame(Game[GameState]):
    """A round in which every seat at once lays one card of its hand face up on the discard.

    This is the engine's exercise rather than a game worth playing: it opens a simultaneous phase,
    closes it a seat at a time, and scores once the last one has acted, which walks `submit`, `advance`
    and `settle` through the branches a real game takes.

    This game is played with a play, and `SealedRoundGame` with a take besides, so the declared type names
    both intents the two of them reach and each states the vocabulary it is played with.
    """

    intents: ClassVar[Intents[Play | Take]] = LAYING

    def zones(self, players: int, deck: Deck) -> Zones:
        return {
            **hands(players),
            "draw": Zone(id="draw", visibility=PILE, ordered=True, cards=to_game_cards(deck, face_down=True)),
            **discard(),
        }

    def _validate_players(self, players: int) -> None:
        if not 2 <= players <= 5:
            raise GameValidationError(f"This game seats 2 to 5 players, and {players} were asked for")

    def _validate_initial_deck(self, deck: Deck) -> None:
        if does_contain_jokers(deck):
            raise GameValidationError("This game is played with suited cards alone")

    def _deal_cards(self, position: Position[GameState], rng: Random) -> Effects[GameState]:
        pile = position.board.zone("draw").cards
        shuffle: Effects[GameState] = (Reorder(zone="draw", order=permutation(len(pile), rng)),)
        deals: Effects[GameState] = tuple(
            MoveCards(source="draw", indices=frozenset(range(HAND_SIZE)), target=hand_of(seat), face_down=True)
            for seat in range(position.players)
        )
        return shuffle + deals

    def _initialize(self, players: int) -> GameState:
        return GameState(phase="deal")

    def _final_validation(self, position: Position[GameState]) -> None:
        short = tuple(
            seat for seat in range(position.players) if len(position.board.zone(hand_of(seat)).cards) != HAND_SIZE
        )
        if short:
            raise GameValidationError(f"Seats {short} hold a hand of some size other than {HAND_SIZE}")

    def validate(self, position: Position[GameState], move: Move) -> None:
        indices = LAYING.read(move).indices
        held = len(position.board.zone(hand_of(move.player)).cards)
        if len(indices) != 1:
            raise IllegalMove(f"Seat {move.player} lays one card at a time, and named {len(indices)}")

        if max(indices) >= held:
            raise IllegalMove(f"Seat {move.player} named position {max(indices)} of a hand holding {held}")

    def expand(self, position: Position[GameState], move: Move, rng: Random) -> Effects[GameState]:
        return (
            MoveCards(
                source=hand_of(move.player),
                indices=LAYING.read(move).indices,
                target="discard",
                face_down=False,
            ),
        )

    def advance(self, position: Position[GameState], move: Move | None, rng: Random) -> Effects[GameState]:
        state = position.state
        if move is not None:
            return (SetState(state=state.with_changes(to_act=state.to_act - {move.player})),)

        if state.phase == "deal":
            return (SetState(state=state.with_changes(phase="play", to_act=range(position.players))),)

        if state.phase == "play" and not state.to_act:
            return (SetState(state=state.with_changes(phase="score", points=self._points(position))),)

        return ()

    def legal_moves(self, position: Position[GameState]) -> Moves:
        return tuple(
            Move(player=seat, action=Play(group="discard", indices=frozenset({index})))
            for seat in sorted(position.state.to_act)
            for index in range(len(position.board.zone(hand_of(seat)).cards))
        )

    def _points(self, position: Position[GameState]) -> Points:
        """A point for every card a seat still holds once the round has closed."""
        return tuple(len(position.board.zone(hand_of(seat)).cards) for seat in range(position.players))


class SealedRoundGame(DiscardGame):
    """A simultaneous round: each seat seals one card face down in its own tray, and every tray turns
    over at once when the last seat has committed.

    A seat may reclaim what it sealed for as long as the round stays open, which is a take-back done as
    an ordinary forward move — a `Take` lifting the card back into the hand and reopening the turn.
    The journal only ever grows, and the tray showed opponents a count where the card sat, so the
    retraction asks no one to forget anything they had been told.

    The right to retract lives in `authorize` and the window it must land inside lives in `validate`,
    which is the split letting an adapter answer one refusal with 403 and the other with 422.
    """

    intents = LAYING_OR_RETRACTING

    def zones(self, players: int, deck: Deck) -> Zones:
        trays = {
            tray_of(seat): Zone(
                id=tray_of(seat),
                owner=seat,
                visibility=HAND,
                ordered=True,
            )
            for seat in range(players)
        }
        return {**super().zones(players, deck), **trays}

    def authorize(self, position: Position[GameState], move: Move) -> None:
        if isinstance(move.action, Take):
            return

        super().authorize(position, move)

    def validate(self, position: Position[GameState], move: Move) -> None:
        if isinstance(move.action, Take):
            self._validate_retraction(position, move.player, move.action)
            return

        super().validate(position, move)

    def expand(self, position: Position[GameState], move: Move, rng: Random) -> Effects[GameState]:
        if isinstance(move.action, Take):
            return (
                MoveCards(
                    source=tray_of(move.player),
                    indices=move.action.indices,
                    target=hand_of(move.player),
                    face_down=True,
                ),
            )

        return (
            MoveCards(
                source=hand_of(move.player),
                indices=LAYING.read(move).indices,
                target=tray_of(move.player),
                face_down=True,
            ),
        )

    def advance(self, position: Position[GameState], move: Move | None, rng: Random) -> Effects[GameState]:
        if move is not None and isinstance(move.action, Take):
            return (SetState(state=position.state.with_changes(to_act=position.state.to_act | {move.player})),)

        if move is None and position.state.phase == "play" and not position.state.to_act:
            return self._reveal(position)

        return super().advance(position, move, rng)

    def _reveal(self, position: Position[GameState]) -> Effects[GameState]:
        """Lay every sealed card face up on the discard and score what the seats held back."""
        turned: Effects[GameState] = tuple(
            MoveCards(
                source=tray_of(seat),
                indices=frozenset(range(len(position.board.zone(tray_of(seat)).cards))),
                target="discard",
                face_down=False,
            )
            for seat in range(position.players)
            if position.board.zone(tray_of(seat)).cards
        )
        return turned + (SetState(state=position.state.with_changes(phase="score", points=self._points(position))),)

    def _validate_retraction(self, position: Position[GameState], player: int, retraction: Take) -> None:
        """Confirm the round is still open and the seat named a card of its own tray.

        Raises:
            IllegalMove: once the round has closed, or when the tray holds no card at that position.
        """
        if position.state.phase != "play":
            raise IllegalMove(f"The {position.state.phase} phase has begun, which settles every sealed card")

        sealed = len(position.board.zone(tray_of(player)).cards)
        if max(retraction.indices) >= sealed:
            raise IllegalMove(f"Seat {player} named position {max(retraction.indices)} of a tray holding {sealed}")


class EndlessGame(DiscardGame):
    """A game whose rules carry the table in a circle, which is what `settle`'s cap answers."""

    def advance(self, position: Position[GameState], move: Move | None, rng: Random) -> Effects[GameState]:
        opposite = "deal" if position.state.phase == "play" else "play"
        return (SetState(state=position.state.with_changes(phase=opposite)),)


class ShortDealGame(DiscardGame):
    """A game whose layout loses a card on the way to the table, which card conservation catches."""

    def zones(self, players: int, deck: Deck) -> Zones:
        laid_out = dict(super().zones(players, deck))
        draw = laid_out["draw"]
        laid_out["draw"] = draw.with_cards(draw.cards[1:])
        return laid_out


class BareGame(Game[GameState]):
    """The least a game may declare: the hooks the engine requires, leaving the optional ones as they come."""

    def zones(self, players: int, deck: Deck) -> Zones:
        return {"draw": Zone(id="draw", visibility=PILE, ordered=True, cards=to_game_cards(deck, face_down=True))}

    def _validate_players(self, players: int) -> None:
        """Any seating this engine accepts suits this game."""

    def _validate_initial_deck(self, deck: Deck) -> None:
        """Any deck this engine accepts suits this game."""

    def _deal_cards(self, position: Position[GameState], rng: Random) -> Effects[GameState]:
        return ()

    def _initialize(self, players: int) -> GameState:
        return GameState(phase="play", to_act=frozenset(range(players)))

    def _final_validation(self, position: Position[GameState]) -> None:
        """The engine's own checks cover everything this game asks of a fresh table."""

    def validate(self, position: Position[GameState], move: Move) -> None:
        """Every intent reaches `expand`, which turns each one into the same nothing."""

    def expand(self, position: Position[GameState], move: Move, rng: Random) -> Effects[GameState]:
        return ()

    def advance(self, position: Position[GameState], move: Move | None, rng: Random) -> Effects[GameState]:
        return ()
