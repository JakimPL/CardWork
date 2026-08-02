from abc import ABC, abstractmethod
from random import Random
from typing import Generic

from cardwork.boards.board import Board
from cardwork.decks.deck import Deck
from cardwork.effects.effect import Effects
from cardwork.effects.fold import fold
from cardwork.exceptions import NotYourTurn, StalePosition, UndoUnavailable
from cardwork.moves.move import Move
from cardwork.positions.position import Position
from cardwork.states.state import StateT
from cardwork.transactions.journal import Journal
from cardwork.transactions.transaction import Transaction
from cardwork.views.position import PositionView
from cardwork.zones.zone import Zones


class Game(ABC, Generic[StateT]):
    _history: list[Position[StateT]]
    _journal: Journal[StateT]
    _players: int
    _published: int
    _rng: Random

    def __init__(
        self,
        players: int,
        deck: Deck,
        *_args: object,
        rng: Random | None = None,
        **_kwargs: object,
    ) -> None:
        self._basic_initial_validation(players, deck)
        self._validate_players(players)
        self._validate_initial_deck(deck)

        origin = Position(
            board=Board(zones=self.zones(players, deck), starting_deck=deck),
            state=self._initialize(players),
            players=players,
        )

        self._players = players
        self._journal = Journal(initial=origin)
        self._history = [origin]
        self._published = 0

        self._rng = rng if rng is not None else Random()

        deal = self._deal_cards(origin, self._rng)
        follow = self.advance(fold(deal, origin))
        self._commit(Transaction(seq=0, move=None, effects=deal + follow))

        self._basic_final_validation()
        self._final_validation(origin)

    @property
    def position(self) -> Position[StateT]:
        return self._history[-1]

    @property
    def state(self) -> StateT:
        return self.position.state

    @property
    def board(self) -> Board:
        return self.position.board

    @property
    def players(self) -> int:
        return self._players

    @property
    def head(self) -> int:
        return self._journal.head

    @property
    def journal(self) -> Journal[StateT]:
        return self._journal

    def view(self, observer: int | None) -> PositionView[StateT]: ...

    def replay(self, upto: int | None = None) -> Position[StateT]:
        return self.journal.replay(upto)

    def undo(self) -> None:
        if self._journal.head <= self._published:
            raise UndoUnavailable(f"transaction {self._journal.head - 1} has been published")

        self._history.pop()
        self._journal = self._journal.truncate()

    def _commit(self, transaction: Transaction[StateT]) -> None:
        self._history.append(fold(transaction.effects, self.position))
        self._journal = self._journal.append(transaction)

    def _transact(self, position: Position[StateT], move: Move, rng: Random) -> Effects[StateT]:
        self.validate(position, move)
        effects = self.expand(position, move, rng)
        return effects + self.advance(fold(effects, position))

    def step(self, position: Position[StateT], move: Move, rng: Random) -> Position[StateT]:
        return fold(self._transact(position, move, rng), position)

    def submit(self, move: Move, base_seq: int) -> Transaction[StateT]:
        if base_seq != self.head:
            raise StalePosition(base_seq, self.head)

        if move.player not in self.state.to_act:
            raise NotYourTurn(move.player, self.state.to_act)

        effects = self._transact(self.position, move, self._rng)
        transaction = Transaction(seq=self.head, move=move, effects=effects)
        self._commit(transaction)
        return transaction

    def mark_published(self) -> None:
        """Called by the adapter after step 10 of §6. Closes everything up to `head` to undo."""
        self._published = self._journal.head

    def _basic_initial_validation(self, players: int, deck: Deck) -> None:
        if players < 1:
            raise ValueError(f"Expected at least 1 player, got {players}")

        if not deck:
            raise ValueError("Deck cannot be empty")

    def _basic_final_validation(self) -> None:
        if self.state.points is None:
            return

        points_table_size = len(self.state.points)
        if self.players != points_table_size:
            raise ValueError(
                f"Points table size {points_table_size} does not match the number of players: {self.players}"
            )

        self.board.validate_board()

    @abstractmethod
    def zones(self, players: int, deck: Deck) -> Zones:
        """Zone layout and visibility policy for this game."""

    @abstractmethod
    def _validate_players(self, players: int) -> None:
        """Conditions on the number of players."""

    @abstractmethod
    def _validate_initial_deck(self, deck: Deck) -> None:
        """Additional checks for supported initial decks."""

    @abstractmethod
    def _deal_cards(self, position: Position[StateT], rng: Random) -> Effects[StateT]:
        """The physical deal: shuffle and distribute. No turn or phase logic."""

    @abstractmethod
    def _initialize(self, players: int) -> StateT:
        """The pre-deal state. Only what is knowable before a card has moved."""

    @abstractmethod
    def _final_validation(self, position: Position[StateT]) -> None:
        """Game-specific checks on the position after the deal."""

    @abstractmethod
    def validate(self, position: Position[StateT], move: Move) -> None:
        """Raise IllegalMove if this move is not permitted."""

    @abstractmethod
    def expand(self, position: Position[StateT], move: Move, rng: Random) -> Effects[StateT]:
        """Translate an intent into primitive effects."""

    @abstractmethod
    def advance(self, position: Position[StateT]) -> Effects[StateT]:
        """Turn/phase transitions, scoring, terminal detection."""

    @abstractmethod
    def legal_moves(self, position: Position[StateT]) -> tuple[Move]:
        """List of legal moves."""
