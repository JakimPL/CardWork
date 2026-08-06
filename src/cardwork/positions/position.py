from __future__ import annotations

from typing import Generic

from pydantic import Field

from cardwork.boards.board import Board
from cardwork.cards.game import CardsOrJokers
from cardwork.models.base import BaseFrozen
from cardwork.states.state import StateT
from cardwork.zones.family import Family


class Position(BaseFrozen, Generic[StateT]):
    """A complete snapshot of a table: every card, the rules cursor, and how many seats are in play.

    Carrying the seat count keeps any position projectable on its own, including one recovered from
    `Journal.replay`, which is what makes "what did player 1 see at move 17?" answerable.

    The seat count is also what a reading across the table stands on, which is why the position answers
    one: a family states the zone every seat holds cards in, and the position reads that family at each
    seat in play. Every such reading goes through the board, so a family the table stands no zone of is
    refused at the reading itself.
    """

    board: Board
    state: StateT
    players: int = Field(ge=1)

    @property
    def seats(self) -> range:
        """The seats in play, in the order the table is read round."""
        return range(self.players)

    def counts(self, family: Family) -> tuple[int, ...]:
        """How many cards each seat holds in one family, in seat order."""
        return tuple(self.board.count(family.of(seat)) for seat in self.seats)

    def held(self, family: Family) -> tuple[CardsOrJokers, ...]:
        """The cards each seat holds in one family, in seat order, as the rules read them."""
        return tuple(self.board.cards(family.of(seat)) for seat in self.seats)

    def holding(self, family: Family) -> frozenset[int]:
        """The seats holding a card in one family, which is what a game still waiting on a seat reads."""
        return frozenset(seat for seat in self.seats if self.board.holds(family.of(seat)))

    def fewest(self, family: Family) -> frozenset[int]:
        """The seats holding the fewest cards in one family, and every one of them where several stand alike.

        A seat that has played its last card holds none, which is the fewest a zone runs to, so a seat
        that went out stands among these. One rule scores either close of a round this way: the award goes
        to the shortest hand at the table, whether a seat went out or the stock ran dry.
        """
        counts = self.counts(family)
        shortest = min(counts)
        return frozenset(seat for seat, count in enumerate(counts) if count == shortest)

    def with_board(self, board: Board) -> Position[StateT]:
        return Position(board=board, state=self.state, players=self.players)

    def with_state(self, state: StateT) -> Position[StateT]:
        return Position(board=self.board, state=state, players=self.players)
