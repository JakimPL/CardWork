from abc import ABC, abstractmethod
from random import Random
from typing import Final, Generic

from cardwork.boards.board import Board
from cardwork.decks.deck import Deck
from cardwork.effects.effects import Effects
from cardwork.effects.fold import fold
from cardwork.exceptions import NotYourTurn, StalePosition, UndoUnavailable
from cardwork.moves.move import Move, Moves
from cardwork.positions.position import Position
from cardwork.states.state import StateT
from cardwork.transactions.journal import Journal
from cardwork.transactions.transaction import Transaction, Transactions
from cardwork.views.event import EventView
from cardwork.views.position import PositionView
from cardwork.views.project import project_position, project_transaction
from cardwork.zones.zone import Zones

SETTLE_LIMIT: Final[int] = 64


class Game(ABC, Generic[StateT]):
    """One table under way: the record of everything committed to it, and the rules driving what may be.

    A game subclasses this with its own state type and fills in the rules hooks — how the table is laid
    out, what a move means, what the rules owe once it lands. The engine keeps the only cursor into
    history, which leaves every hook a pure function of the position it is handed and makes the same
    hooks serve a live table, a replay and a search.

    The surface is wide because this is the single face a driver, an adapter and a solver all talk to:
    reading the table, committing to it, watching it, and the rules hooks a subclass answers.
    """

    _history: list[Position[StateT]]
    _journal: Journal[StateT]
    _published: int
    _rng: Random

    def __init__(
        self,
        players: int,
        deck: Deck,
        *,
        rng: Random | None = None,
    ) -> None:
        self._basic_initial_validation(players, deck)
        self._validate_players(players)
        self._validate_initial_deck(deck)

        origin = Position(
            board=Board(
                zones=self.zones(players, deck),
                starting_deck=deck,
            ),
            state=self._initialize(players),
            players=players,
        )

        self._journal = Journal(initial=origin)
        self._history = [origin]
        self._published = 0
        self._rng = rng if rng is not None else Random()

        deal = self._deal_cards(origin, self._rng)
        effects = deal + self.advance(
            fold(deal, origin),
            None,
            self._rng,
        )

        self._commit(
            Transaction(
                seq=0,
                move=None,
                effects=effects,
            ),
        )

        self._basic_final_validation(self.position)
        self._final_validation(self.position)

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
        return self.position.players

    @property
    def head(self) -> int:
        return self._journal.head

    @property
    def journal(self) -> Journal[StateT]:
        return self._journal

    def view(self, observer: int | None) -> PositionView[StateT]:
        """The table as one observer is entitled to see it, stamped with the sequence it stands at.

        The stamp is what a client quotes back as `base_seq`, which ties the move it submits to the
        position it was looking at, and the moves the view carries are the ones that stamp accepts.

        Args:
            observer: the seat receiving the view, or None for a spectator.
        """
        return project_position(
            self.position,
            self.head,
            observer,
            self.legal_moves(self.position),
        )

    def events(
        self,
        observer: int | None,
        since: int,
    ) -> tuple[EventView[StateT], ...]:
        """Every commit from `since` onward as one observer learns of it, in commit order.

        A client that dropped at a known sequence number reads the stream from there and arrives at the
        knowledge a fresh view would give it, so reconnecting costs what staying connected costs. Each
        event is the difference between two snapshots the engine already holds, and carries the moves the
        later of the two admits, so a client reading the stream is never a round trip behind its options.

        Args:
            observer: the seat receiving the events, or None for a spectator.
            since: the first sequence number to report; must be at least 0.

        Raises:
            ValueError: when `since` is negative.
        """
        if since < 0:
            raise ValueError(f"Events run from sequence 0 onwards, and {since} was asked for")

        return tuple(
            project_transaction(
                transaction,
                self.snapshot(transaction.seq),
                self.snapshot(transaction.seq + 1),
                observer,
                self.legal_moves(self.snapshot(transaction.seq + 1)),
            )
            for transaction in self._journal.transactions[since:]
        )

    def snapshot(self, seq: int) -> Position[StateT]:
        """The position the table stood at once its first `seq` commits had landed, read from memory.

        `replay` derives the same position by folding the journal from its origin; this returns one the
        engine kept as it went, which is what lets an event be built from the pair around a commit.

        Args:
            seq: how many commits the position stands after; must lie between 0 and `head`.

        Raises:
            IndexError: when `seq` names a point beyond the head of the journal.
        """
        if not 0 <= seq <= self.head:
            raise IndexError(f"Sequence {seq} lies outside the range 0..{self.head} the table has reached")

        return self._history[seq]

    def replay(self, upto: int | None = None) -> Position[StateT]:
        return self.journal.replay(upto)

    def submit(self, move: Move, base_seq: int) -> Transaction[StateT]:
        """Commit one seat's move together with the advancement it prompts, and hand back the record.

        The move and its turn change reach the journal as a single transaction, so a client applying
        the event sees the table move and the cursor follow at once.

        Args:
            move: the seat's intent.
            base_seq: the sequence the client built the move on, which pins it to a known position.

        Raises:
            StalePosition: when further commits have landed since `base_seq`.
            NotYourTurn: when `authorize` withholds the turn from this seat.
            IllegalMove: when `validate` rejects what the move asks for.
        """
        if base_seq != self.head:
            raise StalePosition(base_seq, self.head)

        effects = self._transact(self.position, move, self._rng)
        transaction = Transaction(seq=self.head, move=move, effects=effects)
        self._commit(transaction)
        return transaction

    def settle(self) -> Transactions[StateT]:
        """Commit whatever the rules still owe, until the table comes to rest.

        `submit` folds one advancement into the move that prompted it, which leaves the changes a round
        owes once its last seat has acted — the reveal, the scoring, the deal that opens the next hand.
        Each reaches the journal as its own transaction carrying no move, which keeps what a seat did
        legible apart from what the rules did in answer. A table already at rest yields an empty run.

        Raises:
            RuntimeError: when the rules ask for further changes through `SETTLE_LIMIT` commits, which
                marks an `advance` that carries the table round in a circle.
        """
        settled: list[Transaction[StateT]] = []
        for _ in range(SETTLE_LIMIT):
            effects = self.advance(self.position, None, self._rng)
            if not effects:
                return tuple(settled)

            transaction = Transaction(
                seq=self.head,
                move=None,
                effects=effects,
            )
            self._commit(transaction)
            settled.append(transaction)

        raise RuntimeError(f"advance kept asking for changes through {SETTLE_LIMIT} commits without coming to rest")

    def step(
        self,
        position: Position[StateT],
        move: Move,
        rng: Random,
    ) -> Position[StateT]:
        """The position a move leads to, computed apart from the table so a search may explore freely.

        This runs the same rules `submit` runs and touches no engine state, which is what lets a solver
        walk `legal_moves` to any depth on a position the table has yet to reach.

        Raises:
            NotYourTurn: when `authorize` withholds the turn from this seat.
            IllegalMove: when `validate` rejects what the move asks for.
        """
        return fold(self._transact(position, move, rng), position)

    def undo(self) -> None:
        """Drop the commit at the head of the journal, returning the table to the position before it.

        Undo belongs to the operator of a table that has yet to publish anything. A seat that wants its
        move back sends a further move retracting it, which leaves the record every seat reads strictly
        append-only.

        The generator keeps whatever it drew for the dropped commit, so reaching that position again draws
        afresh and may resolve differently — the same move re-submitted, and the same settlement asked for
        a second time, each shuffle and each seat drawn anew. Replay stays exact throughout, since a
        transaction records the outcome of every draw that went into it.

        Raises:
            UndoUnavailable: when every commit the journal holds has already been published.
        """
        if self._journal.head <= self._published:
            raise UndoUnavailable(f"transaction {self._journal.head - 1} has been published")

        self._journal = self._journal.truncate()
        self._history.pop()

    def mark_published(self) -> None:
        """Called by the adapter after step 10 of §6. Closes everything up to `head` to undo."""
        self._published = self._journal.head

    def authorize(self, position: Position[StateT], move: Move) -> None:
        """Confirm the seat behind a move holds the right to act, before the rules read what it asks for.

        Turn policy is the game's to set. The default admits the seats the cursor names; a game widens
        it by overriding this alone — to let a seat retract a commitment while its round is still open,
        or to admit an interrupt from a seat waiting out of turn. Whether such a move comes *in time*
        belongs to `validate`, which keeps a refusal of authority legible apart from one of content.

        Raises:
            NotYourTurn: when the cursor gives the turn to other seats.
        """
        if move.player not in position.state.to_act:
            raise NotYourTurn(move.player, position.state.to_act)

    def legal_moves(self, position: Position[StateT]) -> Moves:  # pylint: disable=unused-argument
        """Every move the rules admit from this position, and an empty run from a game that lists none.

        Enumeration is optional: a game with a wide or awkward move space serves clients that propose a
        move and let `validate` answer. A game that does enumerate gains a searchable engine, since
        `step` turns any move on the list into the position it leads to.
        """
        return ()

    def _commit(self, transaction: Transaction[StateT]) -> None:
        """Record one transaction and the position it produced, keeping the record and the memo in step."""
        position = fold(transaction.effects, self.position)
        self._journal = self._journal.append(transaction)
        self._history.append(position)

    def _transact(
        self,
        position: Position[StateT],
        move: Move,
        rng: Random,
    ) -> Effects[StateT]:
        """The full run of effects one move commits: what it does, followed by what the rules owe after."""
        self.authorize(position, move)
        self.validate(position, move)
        effects = self.expand(position, move, rng)
        return effects + self.advance(fold(effects, position), move, rng)

    def _basic_initial_validation(self, players: int, deck: Deck) -> None:
        if players < 1:
            raise ValueError(f"Expected at least 1 player, got {players}")

        if not deck:
            raise ValueError("Deck cannot be empty")

    def _basic_final_validation(self, position: Position[StateT]) -> None:
        """Confirm the dealt table holds every card it started with and scores the seats it seated.

        Raises:
            ValueError: when the zones hold a multiset of cards apart from the starting deck, or when
                the points table is sized for a different table.
        """
        position.board.validate_board()

        points = position.state.points
        if points is not None and len(points) != position.players:
            raise ValueError(
                f"Points table size {len(points)} does not match the number of players: {position.players}"
            )

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
    def _deal_cards(
        self,
        position: Position[StateT],
        rng: Random,
    ) -> Effects[StateT]:
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
    def expand(
        self,
        position: Position[StateT],
        move: Move,
        rng: Random,
    ) -> Effects[StateT]:
        """Translate an intent into primitive effects."""

    @abstractmethod
    def advance(
        self,
        position: Position[StateT],
        move: Move | None,
        rng: Random,
    ) -> Effects[StateT]:
        """The changes the rules owe once a position is reached: whose turn it becomes, which phase opens, what scores.

        Args:
            position: the position the move's own effects have already been folded into.
            move: the move that led here, and None while the table settles on its own.
            rng: the generator to consume where the rules draw as they carry the table onward — the shuffle
                that opens the next round, the seat that leads it. Every draw reaches the journal inside the
                effect it decided, so replay reproduces it from the record.

        Returns:
            The effects carrying the table onward, and an empty run once it has come to rest.
        """
