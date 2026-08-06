from typing import Annotated, Generic, Literal

from pydantic import Field

from cardwork.decks.deck import GameCards, NonEmptyIndices, Order
from cardwork.effects.effect import Effect
from cardwork.moves.transfer import pop_cards, validate_indices
from cardwork.positions.position import Position
from cardwork.states.state import GameState, StateT
from cardwork.zones.zone import ZoneId


class MoveCards(Effect[StateT], Generic[StateT]):
    """Lift cards out of one zone by position and lay them into another.

    Lifted cards keep their source order, so an unordered set of indices still lands them in a
    determined arrangement.
    """

    kind: Literal["move_cards"] = "move_cards"
    source: ZoneId
    indices: NonEmptyIndices
    target: ZoneId
    at: int | None = Field(default=None, ge=0)
    face_down: bool | None = None

    def apply(self, position: Position[StateT]) -> Position[StateT]:
        board = position.board
        source = board.zone(self.source)
        validate_indices(source.cards, self.indices)
        kept, lifted = pop_cards(source.cards, self.indices)
        moved = self._faced(lifted)

        if self.source == self.target:
            return position.with_board(
                board.with_zones(source.with_cards(self._laid(kept, moved))),
            )

        target = board.zone(self.target)
        return position.with_board(
            board.with_zones(
                source.with_cards(kept),
                target.with_cards(self._laid(target.cards, moved)),
            )
        )

    def _faced(self, cards: GameCards) -> GameCards:
        """The moved cards under this effect's face override, each keeping its own face when none is given."""
        if self.face_down is None:
            return cards

        return tuple(card.with_face(self.face_down) for card in cards)

    def _laid(self, cards: GameCards, moved: GameCards) -> GameCards:
        """The destination contents once the moved cards sit at `at`, or at the end when `at` is None.

        Raises:
            IndexError: when `at` points past the end of the destination.
        """
        if self.at is None:
            return cards + moved

        if self.at > len(cards):
            raise IndexError(f"Insertion index {self.at} exceeds the size {len(cards)} of zone {self.target!r}")

        return cards[: self.at] + moved + cards[self.at :]


class SetFace(Effect[StateT], Generic[StateT]):
    """Turn the addressed cards of one zone to a given face, leaving the rest of the zone as it lies."""

    kind: Literal["set_face"] = "set_face"
    zone: ZoneId
    indices: NonEmptyIndices
    face_down: bool

    def apply(self, position: Position[StateT]) -> Position[StateT]:
        zone = position.board.zone(self.zone)
        validate_indices(zone.cards, self.indices)
        cards = tuple(
            card.with_face(self.face_down) if index in self.indices else card for index, card in enumerate(zone.cards)
        )
        return position.with_board(position.board.with_zones(zone.with_cards(cards)))


class Reorder(Effect[StateT], Generic[StateT]):
    """Lay a zone out in a recorded order, given as the source positions in the order they come to occupy.

    A shuffle reaches the journal as one of these, so a replay reproduces the arrangement from the
    record alone.
    """

    kind: Literal["reorder"] = "reorder"
    zone: ZoneId
    order: Order

    def apply(self, position: Position[StateT]) -> Position[StateT]:
        zone = position.board.zone(self.zone)
        self._validate_order(len(zone.cards))
        cards = tuple(zone.cards[index] for index in self.order)
        return position.with_board(position.board.with_zones(zone.with_cards(cards)))

    def _validate_order(self, size: int) -> None:
        """Confirm the order names every position of a zone holding `size` cards exactly once.

        Raises:
            ValueError: when the order is any sequence other than a permutation of that range.
        """
        if sorted(self.order) != list(range(size)):
            raise ValueError(f"Order {self.order} is not a permutation of the {size} cards in zone {self.zone!r}")


class SetState(Effect[StateT], Generic[StateT]):
    """Replace the rules cursor wholesale with the state this effect carries.

    Carrying the whole state rather than a bag of changes keeps the journal self-describing and lets a
    game's own state subclass survive serialization intact. Build the carried value with
    `GameState.with_changes`, which validates it before it can reach the journal.
    """

    kind: Literal["set_state"] = "set_state"
    state: StateT

    def apply(self, position: Position[StateT]) -> Position[StateT]:
        return position.with_state(self.state)


type AnyEffect[S: GameState] = Annotated[
    MoveCards[S] | SetFace[S] | Reorder[S] | SetState[S],
    Field(discriminator="kind"),
]

type Effects[S: GameState] = tuple[AnyEffect[S], ...]
